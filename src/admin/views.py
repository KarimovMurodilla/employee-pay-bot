import asyncio
import io
import json

import pandas as pd

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from sqladmin import BaseView, ModelView, expose
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload
from starlette.responses import StreamingResponse

from src.db.models.department import Department
from src.db.models.establishment import Establishment
from src.db.models.transaction import Transaction, TransactionStatus
from src.db.models.user import User

from .settings import engine

# --- Other imports and model definitions ---


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.telegram_id,
        User.username,
        User.first_name,
        User.last_name,
        "department",
    ]
    can_create = True
    can_delete = False
    column_searchable_list = [User.username, User.first_name, User.last_name]
    column_details_list = [
        User.id,
        User.telegram_id,
        User.username,
        User.first_name,
        User.last_name,
        User.balance,
        User.daily_limit,
        User.monthly_limit,
        "department",
        "transactions",
    ]
    column_export_list = [
        User.id,
        User.telegram_id,
        User.username,
        User.first_name,
        User.last_name,
        User.balance,
        User.department_id,
    ]
    column_labels = {
        "department": "Department",
    }
    icon = "fa-solid fa-user"
    name_plural = "Foydalanuvchilar"


class DepartmentAdmin(ModelView, model=Department):
    column_list = [Department.id, Department.name, Department.description, "users"]


class EstablishmentAdmin(ModelView, model=Establishment):
    column_list = [
        Establishment.id,
        Establishment.name,
        Establishment.address,
        Establishment.is_active,
        "transactions",
        "owner",
    ]


class TransactionAdmin(ModelView, model=Transaction):
    column_list = [
        Transaction.id,
        Transaction.user_id,
        "user",
        Transaction.establishment_id,
        "establishment",
        Transaction.amount,
        Transaction.type,
        Transaction.status,
        Transaction.created_at,
    ]
    can_create = False
    can_edit = False
    can_delete = False
    column_searchable_list = [Transaction.id, Transaction.user_id]
    column_details_list = [
        Transaction.id,
        "user",
        "establishment",
        Transaction.amount,
        Transaction.type,
        Transaction.status,
        Transaction.description,
        Transaction.receipt_data,
        "creator",
        Transaction.created_at,
    ]
    column_labels = {
        "user": "User",
        "establishment": "Establishment",
    }
    column_export_list = [
        Transaction.id,
        Transaction.user_id,
        Transaction.establishment_id,
        Transaction.amount,
        Transaction.type,
        Transaction.status,
        Transaction.created_at,
    ]


class GlobalStatistics(BaseView):
    name = "Global Statistics"
    icon = "fa-solid fa-chart-line"

    def __init__(self):
        self.async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
        except Exception:
            # Fallback for systems where the font might not be in the local path
            try:
                pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
            except Exception as e:
                print(f"Warning: Could not register DejaVuSans font. PDF export may fail for Cyrillic. Error: {e}")


    @expose("/dashboard", methods=["GET"])
    async def dashboard(self, request):
        async with self.async_session_factory() as session:
            # ✅ Overall company statistics
            total_users_count = await session.scalar(select(func.count(User.id)))
            total_spending = (
                await session.scalar(
                    select(func.sum(Transaction.amount)).where(
                        Transaction.status == TransactionStatus.COMPLETED
                    )
                )
                or 0
            )
            active_establishments_count = await session.scalar(
                select(func.count(Establishment.id)).where(
                    Establishment.is_active == True
                )
            )

            # ✅ Spending by department
            department_spending_query = (
                select(Department.name, func.sum(Transaction.amount))
                .select_from(Department)
                .join(User, User.department_id == Department.id)
                .join(Transaction, Transaction.user_id == User.id)
                .where(Transaction.status == TransactionStatus.COMPLETED)
                .group_by(Department.name)
            )
            department_spending_result = await session.execute(
                department_spending_query
            )
            department_spending = department_spending_result.fetchall()

            # ✅ Spending by establishment
            establishment_spending_query = (
                select(Establishment.name, func.sum(Transaction.amount))
                .select_from(Establishment)
                .join(Transaction, Transaction.establishment_id == Establishment.id)
                .where(Transaction.status == TransactionStatus.COMPLETED)
                .group_by(Establishment.name)
            )
            establishment_spending_result = await session.execute(
                establishment_spending_query
            )
            establishment_spending = establishment_spending_result.fetchall()

            # ✅ Calculate spending percentage by establishment (shares)
            establishment_data_with_shares = []
            for name, spending in establishment_spending:
                share = (spending / total_spending) * 100 if total_spending > 0 else 0
                establishment_data_with_shares.append(
                    {
                        "name": name,
                        "spending": float(spending),
                        "share": round(float(share), 2),
                    }
                )

            # ✅ View all transactions
            all_transactions_query = (
                select(Transaction)
                .options(
                    selectinload(Transaction.user),
                    selectinload(Transaction.establishment),
                )
                .order_by(Transaction.created_at.desc())
            )
            all_transactions_result = await session.execute(all_transactions_query)
            all_transactions = all_transactions_result.scalars().all()

            # ✅ View expenses for each user (by department)
            user_spending_query = (
                select(
                    User,
                    Department.name.label("department_name"),
                    func.sum(Transaction.amount).label("total_spent"),
                )
                .join(Transaction, Transaction.user_id == User.id)
                .join(Department, User.department_id == Department.id, isouter=True)
                .where(Transaction.status == TransactionStatus.COMPLETED)
                .group_by(User.id, Department.name)
                .order_by(func.sum(Transaction.amount).desc())
            )
            user_spending_result = await session.execute(user_spending_query)
            user_spending_by_department = user_spending_result.all()

            # Data for charting (remains unchanged)
            establishment_chart_data = [
                {"name": name, "spending": float(spending)}
                for name, spending in establishment_spending
            ]

            return await self.templates.TemplateResponse(
                request,
                "dashboard.html",
                {
                    "total_users": total_users_count,
                    "total_spending": total_spending,
                    "active_establishments": active_establishments_count,
                    "department_spending": department_spending,
                    "establishment_spending_with_shares": establishment_data_with_shares,
                    "all_transactions": all_transactions,
                    "user_spending_by_department": user_spending_by_department,
                    "establishment_chart_data": json.dumps(establishment_chart_data),
                },
            )

    @expose("/download_stats", methods=["GET"])
    async def download_stats(self, request):
        async with self.async_session_factory() as session:
            format_type = request.query_params.get("format", "excel")

            total_spending_by_department_query = (
                select(Department.name, func.sum(Transaction.amount))
                .select_from(Department)
                .join(User, User.department_id == Department.id)
                .join(Transaction, Transaction.user_id == User.id)
                .group_by(Department.name)
            )
            department_spending = await session.execute(
                total_spending_by_department_query
            )
            department_spending = department_spending.fetchall()

            total_spending_by_establishment_query = (
                select(Establishment.name, func.sum(Transaction.amount))
                .select_from(Establishment)
                .join(Transaction, Transaction.establishment_id == Establishment.id)
                .group_by(Establishment.name)
            )
            establishment_spending = await session.execute(
                total_spending_by_establishment_query
            )
            establishment_spending = establishment_spending.fetchall()

            df_dept = pd.DataFrame(
                department_spending, columns=["Department", "Total Spending"]
            )
            df_est = pd.DataFrame(
                establishment_spending, columns=["Establishment", "Total Spending"]
            )

            output = io.BytesIO()

            df_dept = pd.DataFrame(department_spending, columns=["Отдел", "Сумма расходов"])
            df_est = pd.DataFrame(establishment_spending, columns=["Заведение", "Сумма расходов"])

            if format_type == "excel":
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df_dept.to_excel(
                        writer, sheet_name="Department Spending", index=False
                    )
                    df_est.to_excel(
                        writer, sheet_name="Establishment Spending", index=False
                    )
                output.seek(0)
                return StreamingResponse(
                    output,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={
                        "Content-Disposition": "attachment; filename=statistics.xlsx"
                    },
                )

            elif format_type == "pdf":
                # Use the new, direct PDF generation method
                pdf_buffer = await asyncio.to_thread(
                    self._generate_pdf_report, department_spending, establishment_spending
                )
                return StreamingResponse(
                    pdf_buffer,
                    media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=statistics.pdf"}
                )

            return StreamingResponse(
                io.BytesIO(b"Unsupported format"),
                status_code=400,
                media_type="text/plain",
            )

    def _generate_pdf_report(self, dept_spending: list, est_spending: list) -> io.BytesIO:
        """
        Generates a PDF report from statistics data, writing it to an in-memory buffer.
        """
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Define custom styles using the registered Cyrillic-compatible font
        title_style = styles["Title"]
        title_style.fontName = 'DejaVuSans-Bold'

        header_style = styles["h2"]
        header_style.fontName = 'DejaVuSans-Bold'

        # Main Title
        elements.append(Paragraph("Статистический отчет", title_style))
        elements.append(Spacer(1, 24))

        # Department Spending Table
        elements.append(Paragraph("Расходы по отделам", header_style))
        elements.append(Spacer(1, 12))

        # Manually construct table data with a header row
        dept_table_data = [["Отдел", "Сумма расходов"]]
        for name, spending in dept_spending:
            dept_table_data.append([name, f"{spending:,.2f} UZS"])

        dept_table = Table(dept_table_data, colWidths=[250, 150])
        dept_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'), # Bold header
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),    # Regular body
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(dept_table)
        elements.append(Spacer(1, 24))

        # Establishment Spending Table
        elements.append(Paragraph("Расходы по заведениям", header_style))
        elements.append(Spacer(1, 12))

        # Manually construct table data for the second table
        est_table_data = [["Заведение", "Сумма расходов"]]
        for name, spending in est_spending:
            est_table_data.append([name, f"{spending:,.2f} UZS"])

        est_table = Table(est_table_data, colWidths=[250, 150])
        est_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'), # Bold header
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),    # Regular body
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(est_table)

        doc.build(elements)
        output.seek(0)
        return output


ADMIN_VIEWS = [
    UserAdmin,
    DepartmentAdmin,
    EstablishmentAdmin,
    TransactionAdmin,
    # ReportAdmin,
    GlobalStatistics,
    # BalanceHistoryAdmin,
]
