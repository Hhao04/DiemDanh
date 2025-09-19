from flask import Flask, request, jsonify
from datetime import datetime
import pickle, os, numpy as np
from scipy.spatial.distance import cosine
import pandas as pd
from models import db, Attendance, Student
from utils import get_address_osm

# --- Init Flask ---
app = Flask(__name__)
database_url = os.environ.get('DATABASE_URL')  # Render cung cấp
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# --- Load embeddings ---
with open("embeddings.pkl","rb") as f:
    embeddings_dict = pickle.load(f)
THRESHOLD = 0.5

# --- Load students.csv ---
def load_students_csv():
    if Student.query.first(): return
    df = pd.read_csv("students.csv")
    df.rename(columns={"ID":"student_id","Name":"name","Class":"class_name"}, inplace=True)
    for _, row in df.iterrows():
        s = Student(student_id=row['student_id'], name=row['name'], class_name=row['class_name'])
        db.session.add(s)
    db.session.commit()
    print("Imported students.csv")

# --- Routes ---
@app.route('/checkin', methods=['POST'])
def checkin():
    student_id = request.form.get("student_id")
    subject = request.form.get("subject", "Unknown")
    latitude = float(request.form.get("latitude",0))
    longitude = float(request.form.get("longitude",0))
    embedding_bytes = request.files.get("embedding").read()
    embedding = np.frombuffer(embedding_bytes, dtype=np.float32)

    # So sánh embeddings
    best_score, best_id = 1.0, None
    for sid, emb_template in embeddings_dict.items():
        templates = [emb_template] if not isinstance(emb_template, list) else emb_template
        for te in templates:
            score = cosine(embedding, te)
            if score < best_score:
                best_score, best_id = score, sid
    if best_score > THRESHOLD:
        return jsonify({"status":"failed","message":"Khuôn mặt không hợp lệ", "address":""})

    now = datetime.now()
    address = get_address_osm(latitude, longitude)
    att = Attendance(
        student_id=best_id,
        subject=subject,
        date=now.date(),
        time=now.time(),
        status="present",
        latitude=latitude,
        longitude=longitude,
        address=address
    )
    db.session.add(att)
    db.session.commit()
    return jsonify({
        "status":"present",
        "message":"Điểm danh thành công",
        "date":str(now.date()),
        "time":str(now.time()),
        "subject":subject,
        "address":address
    })

@app.route('/attendance/history', methods=['GET'])
def history():
    student_id = request.args.get("student_id")
    subject = request.args.get("subject")
    q = Attendance.query.filter_by(student_id=student_id)
    if subject: q = q.filter(Attendance.subject==subject)
    records = q.order_by(Attendance.date, Attendance.time).all()
    return jsonify([{
        "student_id": r.student_id,
        "subject": r.subject,
        "date": str(r.date),
        "time": str(r.time),
        "status": r.status,
        "latitude": r.latitude,
        "longitude": r.longitude,
        "address": r.address
    } for r in records])

@app.route('/attendance/export_excel', methods=['GET'])
def export_excel():
    class_name = request.args.get("class")
    subject = request.args.get("subject")
    date = request.args.get("date")
    q = db.session.query(Attendance, Student).join(Student, Attendance.student_id==Student.student_id)
    if class_name: q = q.filter(Student.class_name==class_name)
    if subject: q = q.filter(Attendance.subject==subject)
    if date: q = q.filter(Attendance.date==date)
    df = pd.DataFrame([{
        "student_id": a.Attendance.student_id,
        "name": a.Student.name,
        "class": a.Student.class_name,
        "subject": a.Attendance.subject,
        "date": str(a.Attendance.date),
        "time": str(a.Attendance.time),
        "status": a.Attendance.status,
        "latitude": a.Attendance.latitude,
        "longitude": a.Attendance.longitude,
        "address": a.Attendance.address
    } for a in q.all()])
    filename = f"export_{class_name}_{subject}_{date}.xlsx"
    df.to_excel(filename, index=False)
    return jsonify({"status":"success","file":filename})

# --- Run ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        load_students_csv()
    app.run(host='0.0.0.0', port=5000)
