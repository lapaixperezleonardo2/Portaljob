from flask import Flask, render_template, request, redirect, session, flash, send_from_directory
from flask_cors import CORS
from backend.database import get_connection
from werkzeug.utils import secure_filename
import os
import uuid

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "frontend"),
    static_folder=os.path.join(BASE_DIR, "frontend")
)

app.secret_key = "clave_secreta"
CORS(app)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "backend/uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.context_processor
def inject_user():
    return dict(user_name=session.get("name"))


# =========================
# HOME
# =========================
@app.route("/")
def home():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    search = request.args.get("search")
    location = request.args.get("location")
    salary = request.args.get("salary")

    query = """
    SELECT jobs.*,
    (
        SELECT COUNT(*)
        FROM applications
        WHERE applications.job_id = jobs.id
    ) AS total_applications
    FROM jobs
    WHERE 1=1
    """

    params = []

    if search:
        query += " AND (title LIKE %s OR location LIKE %s OR company LIKE %s OR description LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])

    if location:
        query += " AND location=%s"
        params.append(location)

    if salary:
        query += " AND salary >= %s"
        params.append(salary)

    cursor.execute(query, tuple(params))
    jobs = cursor.fetchall()

    applied_jobs = []
    favorite_jobs = []

    if "user_id" in session:
        user_id = session["user_id"]

        cursor.execute("SELECT job_id FROM applications WHERE user_id=%s", (user_id,))
        applied_jobs = [r["job_id"] for r in cursor.fetchall()]

        cursor.execute("SELECT job_id FROM favorites WHERE user_id=%s", (user_id,))
        favorite_jobs = [r["job_id"] for r in cursor.fetchall()]

    conn.close()

    return render_template("index.html",
                           jobs=jobs,
                           applied_jobs=applied_jobs,
                           favorite_jobs=favorite_jobs)


# =========================
# AUTH PAGES
# =========================
@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/jobs")
def jobs_page():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("jobs.html")


@app.route("/profile")
def profile_page():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()

    cursor.execute("SELECT name FROM skills WHERE user_id=%s", (user_id,))
    skills = cursor.fetchall()

    conn.close()

    return render_template("profile.html", user=user, skills=skills)


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    last_name = request.form.get("last_name")
    email = request.form["email"]
    password = request.form["password"]
    birth_date = request.form.get("birth_date")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (name, last_name, email, password, birth_date)
        VALUES (%s,%s,%s,%s,%s)
    """, (name, last_name, email, password, birth_date))

    conn.commit()
    conn.close()

    return redirect("/login")


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form["email"]
    password = request.form["password"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        return redirect("/")
    else:
        flash("Credenciales incorrectas", "error")
        return redirect("/login")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# =========================
# JOB DETAIL
# =========================
@app.route("/job/<int:id>")
def job_detail(id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM jobs WHERE id=%s", (id,))
    job = cursor.fetchone()

    conn.close()

    return render_template("job-detail.html", job=job)


# =========================
# CREATE JOB
# =========================
@app.route("/create-job", methods=["POST"])
def create_job():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO jobs (title, description, salary, location, user_id, company, job_type, requirements, benefits)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        request.form["title"],
        request.form["description"],
        request.form["salary"],
        request.form["location"],
        session["user_id"],
        request.form["company"],
        request.form["job_type"],
        request.form["requirements"],
        request.form["benefits"]
    ))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/create-job-page")
def create_job_page():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("create-job.html")


# =========================
# FAVORITES
# =========================
@app.route("/favorite/<int:job_id>", methods=["POST"])
def favorite(job_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT IGNORE INTO favorites (user_id, job_id) VALUES (%s,%s)",
                   (session["user_id"], job_id))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/favorites")
def favorites_page():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT jobs.*
        FROM favorites
        JOIN jobs ON favorites.job_id = jobs.id
        WHERE favorites.user_id=%s
    """, (session["user_id"],))

    jobs = cursor.fetchall()
    conn.close()

    return render_template("favorites.html", jobs=jobs)


# =========================
# APPLY
# =========================
@app.route("/apply/<int:job_id>", methods=["POST"])
def apply(job_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("INSERT INTO applications (user_id, job_id) VALUES (%s,%s)",
                   (session["user_id"], job_id))

    conn.commit()
    conn.close()

    flash("Postulación enviada", "success")
    return redirect("/")


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)