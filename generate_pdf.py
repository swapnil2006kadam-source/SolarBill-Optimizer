from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
import os
from datetime import datetime


def create_pdf(filename, report):

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    title = styles["Title"]
    title.alignment = TA_CENTER

    heading = styles["Heading2"]
    heading.alignment = TA_CENTER

    story = []

    # ------------------------
    # Logo
    # ------------------------

    logo = "static/logo.png"

    if os.path.exists(logo):
        img = Image(logo, width=70, height=70)
        img.hAlign = "CENTER"
        story.append(img)

    # ------------------------
    # Title
    # ------------------------

    story.append(Paragraph("SolarBill Optimizer", title))
    story.append(
        Paragraph(
            "Electricity Bill Analysis Report",
            heading
        )
    )

    story.append(Spacer(1,20))

    # ------------------------
    # Table
    # ------------------------

    data = [

        ["Customer", report["user_name"]],

        ["CA Number", report["ca_number"]],

        ["Bill Month", report["bill_month"]],

        ["Units", report["units"]],

        ["Bill Amount", f"₹ {report['bill_amount']}"],

        ["Recommended Solar", f"{report['solar_kw']} kW"],

        ["Monthly Savings", f"₹ {report['monthly_savings']}"],

        ["Yearly Savings", f"₹ {report['yearly_savings']}"],

        ["Govt Subsidy", f"₹ {report['subsidy']}"],

        ["Installation Cost", f"₹ {report['installation_cost']}"],

        ["After Subsidy", f"₹ {report['final_cost']}"],

        ["ROI", f"{report['roi']} Years"]

    ]

    table = Table(data, colWidths=[190,260])

    table.setStyle(

        TableStyle([

            ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#2563eb")),
            ("TEXTCOLOR",(0,0),(0,-1),colors.white),

            ("BACKGROUND",(1,0),(1,-1),colors.whitesmoke),

            ("GRID",(0,0),(-1,-1),1,colors.grey),

            ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),

            ("BOTTOMPADDING",(0,0),(-1,-1),10),

            ("TOPPADDING",(0,0),(-1,-1),10)

        ])

    )

    story.append(table)

    story.append(Spacer(1,25))

    # ------------------------
    # Tips
    # ------------------------

    story.append(Paragraph("<b>Energy Saving Tips</b>", styles["Heading2"]))

    story.append(
        Paragraph(
            """
            • Switch to LED bulbs<br/>
            • Use Energy Efficient Appliances<br/>
            • Turn Off Standby Devices<br/>
            • Install Rooftop Solar Panels
            """,
            styles["BodyText"]
        )
    )

    story.append(Spacer(1,30))

    # ------------------------
    # Footer
    # ------------------------

    story.append(
        Paragraph(
            f"Generated on : {datetime.now().strftime('%d-%m-%Y %H:%M')}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            "<b>Powered by SolarBill Optimizer</b>",
            styles["Heading3"]
        )
    )

    doc.build(story)