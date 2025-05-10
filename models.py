from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_numbers = db.Column(db.String, nullable=False)  # ذخیره شماره‌ها به صورت رشته
    birthdate = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    image_path = db.Column(db.String, nullable=True)

    def __repr__(self):
        return f'<Contact {self.first_name} {self.last_name}>'
