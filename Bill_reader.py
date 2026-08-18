import pdfplumber
import re


def read_bill(pdf_path):

    text = ""

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text


import re

def extract_bill_data(text):

    data = {}

    # CA Number
    ca = re.search(r'CA\s*NO[:\s]*([0-9]+)', text, re.IGNORECASE)

    data["ca_number"] = ca.group(1) if ca else "Not Found"

    # Bill Month
    month = re.search(r'\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)-\d{2}\b', text)

    data["bill_month"] = month.group(0) if month else "Not Found"



    # Units Consumed
    units = re.search(
        r'Bill\s*Month\s*Units\s*Consumed.*?\n\s*[A-Z]{3}-\d{2}\s+(\d+)',
        text,
        re.DOTALL
    )

    data["units"] = int(units.group(1)) if units else 0

    # Total Bill Amount
    amount = re.search(
        r'Total\s*bill\s*amount\s*\(A\+B\+C\)\s*([0-9]+\.[0-9]{2})',
        text,
        re.IGNORECASE
    )

    data["bill_amount"] = float(amount.group(1)) if amount else 0.0
    return data
