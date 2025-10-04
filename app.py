from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime
from werkzeug.utils import secure_filename
from datetime import datetime
import os

# ---------- SQLAlchemy Base ----------
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# ---- SECRET KEY (FIXED) ----
# NOTE: isko stable rakho (har run pe random mat banao)
app.config["SECRET_KEY"] = "change_this_to_a_long_random_string_once"

# ---------- DB ----------
os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, "amdc_python_interview.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ---------- Uploads ----------
UPLOAD_ROOT = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_ROOT, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_ROOT

ALLOWED_EXTS = {"pdf", "png", "jpg", "jpeg", "doc", "docx"}
def allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTS

db.init_app(app)

# ---------- Model ----------
class UserDetails(db.Model):
    __tablename__ = "user_details"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email_id: Mapped[str] = mapped_column(String(200), nullable=False)
    phone_no: Mapped[int] = mapped_column(Integer, nullable=False)
    year_of_exp: Mapped[int] = mapped_column(Integer, nullable=False)
    date_of_birth: Mapped[str] = mapped_column(String(200), nullable=False)
    highest_degree: Mapped[str] = mapped_column(String(200), nullable=False)
    stream_of_degree: Mapped[str] = mapped_column(String(200), nullable=False)
    current_location: Mapped[str] = mapped_column(String(200), nullable=False)
    aadhaar_path: Mapped[str] = mapped_column(String(500), nullable=True)
    resume_path:  Mapped[str] = mapped_column(String(500), nullable=True)
    marks_obtained:  Mapped[int] = mapped_column(Integer, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, default=None)

with app.app_context():
    db.create_all()

# ---------- Answer Key (Q1..Q35) ----------
ANSWER_KEY = {
    "q1":"B","q2":"C","q3":"B","q4":"B","q5":"B",
    "q6":"C","q7":"B","q8":"B","q9":"A","q10":"B",
    "q11":"B","q12":"B","q13":"B","q14":"C","q15":"B",
    "q16":"B","q17":"A","q18":"A","q19":"A","q20":"A",
    "q21":"B","q22":"B","q23":"A","q24":"B","q25":"B",
    "q26":"C","q27":"B","q28":"C","q29":"C","q30":"B",
    "q31":"A","q32":"B","q33":"B","q34":"B","q35":"B"
}

# ---------------- ROUTES ----------------

# ✅ SINGLE home route (endpoint name = user_details)
@app.route("/", methods=["GET"])
def user_details():
    return render_template("user_details.html")

# ✅ Submit details (DB + files + session) → success.html
@app.route("/submit_details", methods=["POST"])
def submit_details():
    full_name        = request.form.get("full_name", "").strip()
    email_id         = request.form.get("email_id", "").strip()
    phone_no         = request.form.get("phone_no", "").strip()
    year_of_exp      = request.form.get("year_of_exp", "").strip()
    date_of_birth    = request.form.get("date_of_birth", "").strip()
    highest_degree   = request.form.get("highest_degree", "").strip()
    stream_of_degree = request.form.get("stream_of_degree", "").strip()
    current_location = request.form.get("current_location", "").strip()

    if not full_name or not email_id or not date_of_birth:
        return "Required fields missing", 400

    aadhaar_file = request.files.get("aadhaar")
    resume_file  = request.files.get("resume")

    safe_name = "_".join(full_name.split())
    safe_dob  = date_of_birth.replace("-", "_")
    user_folder = os.path.join(app.config["UPLOAD_FOLDER"], f"{safe_name}_{safe_dob}")
    os.makedirs(user_folder, exist_ok=True)

    aadhaar_path = None
    resume_path  = None

    if aadhaar_file and aadhaar_file.filename:
        fn = secure_filename(aadhaar_file.filename)
        if not allowed(fn): return "Aadhaar file type not allowed", 400
        aadhaar_path = os.path.join(user_folder, f"aadhaar_{fn}")
        aadhaar_file.save(aadhaar_path)

    if resume_file and resume_file.filename:
        fn = secure_filename(resume_file.filename)
        if not allowed(fn): return "Resume file type not allowed", 400
        resume_path = os.path.join(user_folder, f"resume_{fn}")
        resume_file.save(resume_path)

    try:
        new_user = UserDetails(
            full_name=full_name,
            email_id=email_id,
            phone_no=phone_no,
            year_of_exp=int(year_of_exp),
            date_of_birth=date_of_birth,
            highest_degree=highest_degree,
            stream_of_degree=stream_of_degree,
            current_location=current_location,
            aadhaar_path=aadhaar_path,
            resume_path=resume_path
        )
        db.session.add(new_user)
        db.session.commit()

        # Save to session for quiz
        session["user_id"] = new_user.id
        session["full_name"] = full_name

        return render_template("success.html", full_name=full_name)
    except Exception as e:
        db.session.rollback()
        return f"Error saving details: {e}", 500

# ✅ Quiz page
@app.route("/quiz", methods=["GET"])
def quiz():
    name = session.get("full_name", "Candidate")
    return render_template("interviewQuestions0to4.html", full_name=name)

# ✅ Submit quiz: score + update DB → test_complete.html
@app.route("/submit_quiz", methods=["POST"])
def submit_quiz():
    # collect answers
    answers = {f"q{i}": request.form.get(f"q{i}") for i in range(1, 36)}
    # score
    score = sum(1 for k, v in ANSWER_KEY.items() if answers.get(k) == v)

    # update DB row for this user
    uid = session.get("user_id")
    user = db.session.get(UserDetails, uid) if uid else None
    if user:
        user.marks_obtained = score
        user.submitted_at = datetime.utcnow()
        db.session.commit()

    name = session.get("full_name", "Candidate")
    return render_template("test_complete.html", finished=True, full_name=name, score=score)

# ✅ Timer-timeout landing page (no submit)
@app.route("/test-complete", methods=["GET"])
def test_complete():
    name = session.get("full_name", "Candidate")
    return render_template("test_complete.html", finished=False, full_name=name, score=None)

if __name__ == "__main__":
    app.run(debug=True, port=8000)
