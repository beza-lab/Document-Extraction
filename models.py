from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    vendor = db.Column(db.String(200))

    invoice_no = db.Column(db.String(100))

    invoice_date = db.Column(db.String(50))

    amount = db.Column(db.Float)

    filename = db.Column(db.String(255))