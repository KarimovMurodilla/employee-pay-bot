from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def write_revenue_pdf(data: dict, filename="revenue_summary.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Заголовок
    elements.append(Paragraph(f"Revenue Summary for {data['name']}", styles["Title"]))
    elements.append(Spacer(1, 20))

    # Таблица данных
    table_data = [
        ["Establishment ID", data["establishment_id"]],
        ["Name", data["name"]],
        ["Total Revenue", f"${data['total_revenue']:.2f}"],
        ["Today Revenue", f"${data['today_revenue']:.2f}"],
        ["Total Orders", data["total_orders"]],
        ["Average Order Value", f"${data['average_order_value']:.2f}"],
    ]

    table = Table(table_data, colWidths=[150, 250])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )

    elements.append(table)
    doc.build(elements)
    return True


# # Пример использования
# data = {
#     "establishment_id": 1,
#     "name": "Cafe Mocha",
#     "total_revenue": 1200.50,
#     "today_revenue": 150.75,
#     "total_orders": 30,
#     "average_order_value": 40.02,
# }
# write_revenue_pdf(data)
