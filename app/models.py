from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_numbers = db.Column(db.String, nullable=False)
    birthdate = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    image_path = db.Column(db.String, nullable=True)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    adjust_day = db.Column(db.INTEGER, default=0)
