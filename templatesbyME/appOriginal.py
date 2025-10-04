from flask import Flask, render_template, request ,session   
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from werkzeug.utils import secure_filename
import os
import secrets
from datetime import datetime
from sqlalchemy import DateTime



# ---------- SQLAlchemy Base ----------
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)


os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, "amdc_python_interview.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = secrets.token_hex(16)


print(f"The path of db is created as :{db_path}") 


UPLOAD_ROOT = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_ROOT, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_ROOT
print(f"The location of upload path is : {UPLOAD_ROOT}")

print("(optional) allow only few extensions") 
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
    date_of_birth: Mapped[str] = mapped_column(String(200), nullable=False)
    highest_degree: Mapped[str] = mapped_column(String(200), nullable=False)
    stream_of_degree: Mapped[str] = mapped_column(String(200), nullable=False)
    current_location: Mapped[str] = mapped_column(String(200), nullable=False)
    aadhaar_path: Mapped[str] = mapped_column(String(500), nullable=True)
    resume_path:  Mapped[str] = mapped_column(String(500), nullable=True)
    marks_obtained:  Mapped[Integer] = mapped_column(Integer, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, default=datetime.utcnow)


with app.app_context():
    db.create_all()


@app.route("/", methods=["GET"])
def form_page():
    return render_template("user_details.html")

@app.route("/submit_details", methods=["POST"])
def submit_details():
    full_name        = request.form.get("full_name", "").strip()
    email_id         = request.form.get("email_id", "").strip()
    date_of_birth    = request.form.get("date_of_birth", "").strip()  
    highest_degree   = request.form.get("highest_degree", "").strip()
    stream_of_degree = request.form.get("stream_of_degree", "").strip()
    current_location = request.form.get("current_location", "").strip()

    if not full_name or not email_id or not date_of_birth:
        return " Required fields missing", 400

    
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
        if not allowed(fn):
            return " Aadhaar file type not allowed", 400
        aadhaar_path = os.path.join(user_folder, f"aadhaar_{fn}")
        aadhaar_file.save(aadhaar_path)

    if resume_file and resume_file.filename:
        fn = secure_filename(resume_file.filename)
        if not allowed(fn):
            return " Resume file type not allowed", 400
        resume_path = os.path.join(user_folder, f"resume_{fn}")
        resume_file.save(resume_path)
        
    try:
        new_user = UserDetails(
            full_name=full_name,
            email_id=email_id,
            date_of_birth=date_of_birth,
            highest_degree=highest_degree,
            stream_of_degree=stream_of_degree,
            current_location=current_location,
            aadhaar_path=aadhaar_path,
            resume_path=resume_path
        )
        db.session.add(new_user)
        db.session.commit()
         # ✅ Save name in session for later pages (like quiz)
        session["full_name"] = full_name
        # return " User details & files saved successfully!"
        return render_template("success.html",full_name=full_name)
    except Exception as e:
        db.session.rollback()
        return f" Error saving details: {e}", 500

@app.route("/quiz", methods=["GET"])
def quiz():
    name = session.get("full_name")
    return render_template("interviewQuestions0to4.html",full_name=name)

@app.route("/", methods=["GET"])
def user_details():
    return render_template("user_details.html")

@app.route("/submit_details", methods=["GET"])
def come_to_success_page():
    return render_template("success.html")


@app.route("/submit_quiz", methods=["POST"])
def submit_quiz():
    name = session.get("full_name", "Candidate")
    return render_template("test_complete.html", finished=True, full_name=name)

# Timer timeout landing page
@app.route("/test-complete", methods=["GET"])
def test_complete():
    name = session.get("full_name", "Candidate")
    return render_template("test_complete.html", finished=False, full_name=name)





if __name__ == "__main__":
    app.run(debug=True, port=8000)  