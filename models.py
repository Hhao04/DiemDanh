from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = "students"
    student_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)

    # Quan hệ với điểm danh
    attendances = db.relationship("Attendance", back_populates="student")


class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), db.ForeignKey("students.student_id"))
    subject = db.Column(db.String(50))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    status = db.Column(db.String(20))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    address = db.Column(db.String(200))

    # Quan hệ với sinh viên
    student = db.relationship("Student", back_populates="attendances")


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' hoặc 'teacher'
    student_id = db.Column(db.String(20), db.ForeignKey("students.student_id"), nullable=True)

    # Quan hệ tùy chọn với sinh viên
    student = db.relationship("Student")
