from flask import Flask, render_template, request
from models import db, Invoice
import os
import pandas as pd
import pdfplumber
import re

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///invoice.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Initialize database
db.init_app(app)

with app.app_context():
    db.create_all()


# PDF Reader Function
def read_pdf(filepath):

    text = ""

    with pdfplumber.open(filepath) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text

def extract_data(text):

    vendor = "Unknown"
    invoice_no = ""
    invoice_date = ""
    amount = 0

    lines = text.split("\n")

    # Vendor = usually first non-empty line
    for line in lines:
        if line.strip():
            vendor = line.strip()
            break

    # Receipt / Invoice Number
    invoice_match = re.search(
        r"(Receipt|Invoice)\s*(No|#)?[: ]*\s*([A-Za-z0-9\-]+)",
        text,
        re.IGNORECASE
    )

    if invoice_match:
        invoice_no = invoice_match.group(3)

    # Date
    date_match = re.search(
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        text
    )

    if date_match:
        invoice_date = date_match.group(1)

    # Total Amount
    amount_match = re.search(
        r"(Total|Grand Total|Amount)[: ]*\s*([\d,]+\.?\d*)",
        text,
        re.IGNORECASE
    )

    if amount_match:
        amount = float(
            amount_match.group(2).replace(",", "")
        )

    return vendor, invoice_no, invoice_date, amount


# Home Page
@app.route("/")
def home():

    return render_template("index.html")


# Upload PDF
@app.route("/upload", methods=["POST"])
def upload():

    file = request.files["invoice"]

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(filepath)

    # Read PDF text
    text = read_pdf(filepath)

    vendor, invoice_no, invoice_date, amount = extract_data(text)

    print("Vendor:", vendor)
    print("Invoice:", invoice_no)
    print("Date:", invoice_date)
    print("Amount:", amount)


    invoice = Invoice(
        vendor=vendor,
        invoice_no=invoice_no,
        invoice_date=invoice_date,
        amount=amount,
        filename=file.filename
    )

    db.session.add(invoice)
    db.session.commit()

    return "Uploaded Successfully"


# Show Invoices
@app.route("/invoices")
def invoices():

    all_invoices = Invoice.query.all()

    return render_template(
        "invoices.html",
        invoices=all_invoices
    )


# Export Excel
@app.route("/export")
def export():

    invoices = Invoice.query.all()

    data = []

    for i in invoices:

        data.append({
            "Vendor": i.vendor,
            "Invoice No": i.invoice_no,
            "Date": i.invoice_date,
            "Amount": i.amount,
            "File Name": i.filename
        })

    df = pd.DataFrame(data)

    df.to_excel(
        "reports/invoices.xlsx",
        index=False
    )

    return "Excel Exported Successfully"


if __name__ == "__main__":
    app.run(debug=True)