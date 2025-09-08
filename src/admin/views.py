import io
from collections import defaultdict
from datetime import datetime
from typing import List, Any, Tuple
import pandas as pd
from sqladmin import ModelView, BaseView, expose
from sqlalchemy import func, select
from starlette.responses import StreamingResponse, FileResponse
import os
import json
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload
from .settings import engine
from .settings import engine

from src.db.models.department import Department
from src.db.models.establishment import Establishment
from src.db.models.transaction import Transaction, TransactionStatus
from src.db.models.user import User


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.telegram_id, User.username, User.first_name, User.last_name, "department",]
    can_create = True
    can_delete = False
    column_searchable_list = [User.username, User.first_name, User.last_name]
    column_details_list = [User.id, User.telegram_id, User.username, User.first_name, User.last_name, User.balance, User.daily_limit, User.monthly_limit, "department", "transactions",]
    column_export_list = [User.id, User.telegram_id, User.username, User.first_name, User.last_name, User.balance, User.department_id]
    column_labels = {
        "department": "Department",
    }
    icon = "fa-solid fa-user"
    name_plural = "Foydalanuvchilar"


class DepartmentAdmin(ModelView, model=Department):
    column_list = [Department.id, Department.name, Department.description, "users"]


class EstablishmentAdmin(ModelView, model=Establishment):
    column_list = [Establishment.id, Establishment.name, Establishment.address, Establishment.is_active, "transactions", "owner"]
    can_create = False
    can_delete = False


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


    @expose("/dashboard", methods=["GET"])
    async def dashboard(self, request):
        async with self.async_session_factory() as session:
            # ✅ Overall company statistics
            total_users_count = await session.scalar(select(func.count(User.id)))
            total_spending = await session.scalar(
                select(func.sum(Transaction.amount)).where(Transaction.status == TransactionStatus.COMPLETED)
            ) or 0
            active_establishments_count = await session.scalar(select(func.count(Establishment.id)).where(Establishment.is_active == True))

            # ✅ Spending by department
            department_spending_query = (
                select(Department.name, func.sum(Transaction.amount))
                .select_from(Department)
                .join(User, User.department_id == Department.id)
                .join(Transaction, Transaction.user_id == User.id)
                .where(Transaction.status == TransactionStatus.COMPLETED)
                .group_by(Department.name)
            )
            department_spending_result = await session.execute(department_spending_query)
            department_spending = department_spending_result.fetchall()
            
            # ✅ Spending by establishment
            establishment_spending_query = (
                select(Establishment.name, func.sum(Transaction.amount))
                .select_from(Establishment)
                .join(Transaction, Transaction.establishment_id == Establishment.id)
                .where(Transaction.status == TransactionStatus.COMPLETED)
                .group_by(Establishment.name)
            )
            establishment_spending_result = await session.execute(establishment_spending_query)
            establishment_spending = establishment_spending_result.fetchall()

            # ✅ Calculate spending percentage by establishment (shares)
            establishment_data_with_shares = []
            for name, spending in establishment_spending:
                share = (spending / total_spending) * 100 if total_spending > 0 else 0
                establishment_data_with_shares.append({
                    "name": name,
                    "spending": float(spending),
                    "share": round(float(share), 2)
                })

            # ✅ View all transactions
            all_transactions_query = (
                select(Transaction)
                .options(
                    selectinload(Transaction.user), 
                    selectinload(Transaction.establishment)
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
                    func.sum(Transaction.amount).label("total_spent")
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
            establishment_chart_data = [{"name": name, "spending": float(spending)} for name, spending in establishment_spending]

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
            department_spending = await session.execute(total_spending_by_department_query)
            department_spending = department_spending.fetchall()

            total_spending_by_establishment_query = (
                select(Establishment.name, func.sum(Transaction.amount))
                .select_from(Establishment)
                .join(Transaction, Transaction.establishment_id == Establishment.id)
                .group_by(Establishment.name)
            )
            establishment_spending = await session.execute(total_spending_by_establishment_query)
            establishment_spending = establishment_spending.fetchall()

            df_dept = pd.DataFrame(department_spending, columns=["Department", "Total Spending"])
            df_est = pd.DataFrame(establishment_spending, columns=["Establishment", "Total Spending"])

            output = io.BytesIO()

            if format_type == "excel":
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_dept.to_excel(writer, sheet_name="Department Spending", index=False)
                    df_est.to_excel(writer, sheet_name="Establishment Spending", index=False)
                output.seek(0)
                return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=statistics.xlsx"})
            
            elif format_type == "pdf":
                # Для генерации PDF вам потребуется дополнительная библиотека, например, Reportlab.
                # Эта часть кода является заглушкой.
                return StreamingResponse(
                    io.BytesIO(b"PDF generation is not implemented yet. Please use Excel."),
                    status_code=400,
                    media_type="text/plain",
                )
            
            return StreamingResponse(
                io.BytesIO(b"Unsupported format"),
                status_code=400,
                media_type="text/plain",
            )


ADMIN_VIEWS = [
    UserAdmin,
    DepartmentAdmin,
    EstablishmentAdmin,
    TransactionAdmin,
    # ReportAdmin,
    GlobalStatistics,
    # BalanceHistoryAdmin,
]
