from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String, nullable=False)
    subject = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String, nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    address = db.Column(db.String)

class Student(db.Model):
    student_id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    class_name = db.Column(db.String)
