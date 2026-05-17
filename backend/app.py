from flask import Flask, render_template, request, redirect, session, flash
from flask_cors import CORS
from flask import send_from_directory
from backend.database import get_connection
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid

filename = f"{uuid.uuid4()}.pdf"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "../frontend"),
    static_folder=os.path.join(BASE_DIR, "../frontend")
)

app.secret_key = "clave_secreta"  # 🔐 NECESARIO
CORS(app)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
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

        cursor.execute(
            "SELECT job_id FROM applications WHERE user_id=%s",
            (user_id,)
        )
        applied_jobs = [row["job_id"] for row in cursor.fetchall()]

        cursor.execute(
            "SELECT job_id FROM favorites WHERE user_id=%s",
            (user_id,)
        )
        favorite_jobs = [row["job_id"] for row in cursor.fetchall()]

    conn.close()

    return render_template(
        "index.html",
        jobs=jobs,
        applied_jobs=applied_jobs,
        favorite_jobs=favorite_jobs
    )

# =========================
# CANCELAR POSTULACION
# =========================
@app.route("/cancel/<int:job_id>", methods=["POST"])
def cancel_application(job_id):
    if "user_id" not in session:
        return redirect("/login.html")

    user_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM applications WHERE user_id=%s AND job_id=%s",
        (user_id, job_id)
    )

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/login.html")
def login_page():
    return render_template("login.html")

@app.route("/register.html")
def register_page():
    return render_template("register.html")

@app.route("/jobs.html")
def jobs_page():
    return render_template("jobs.html")


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    last_name = request.form.get("last_name")  # opcional
    email = request.form["email"]
    password = request.form["password"]
    birth_date = request.form.get("birth_date")  # opcional

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (name, last_name, email, password, birth_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, last_name, email, password, birth_date))

    conn.commit()
    conn.close()

    return redirect("/login.html")


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE email=%s AND password=%s",
        (email, password)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        return redirect("/")
    else:
        flash("Usuario y cuenta no encontrados ❌","error")
        return redirect("/profile.html")

# =========================
# PROFILE
# =========================
@app.route("/profile.html")
def profile_page():
    if "user_id" not in session:
        return redirect("/login.html")

    user_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()

    # 🔥 habilidades
    cursor.execute("SELECT name FROM skills WHERE user_id=%s", (user_id,))
    skills = cursor.fetchall()

    conn.close()

    return render_template("profile.html", user=user, skills=skills)

@app.route("/update-skills", methods=["POST"])
def update_skills():
    if "user_id" not in session:
        return redirect("/login.html")

    user_id = session["user_id"]
    skills = request.form.get("skills")  # "HTML,CSS,JS"

    conn = get_connection()
    cursor = conn.cursor()

    # 🔥 borrar habilidades anteriores
    cursor.execute("DELETE FROM skills WHERE user_id=%s", (user_id,))

    # 🔥 insertar nuevas habilidades
    if skills:
        skills_list = skills.split(",")

        for skill in skills_list:
            cursor.execute(
                "INSERT INTO skills (user_id, name) VALUES (%s, %s)",
                (user_id, skill.strip())
            )

    conn.commit()
    conn.close()

    flash("Habilidades actualizadas 🚀")
    return redirect("/profile.html")

@app.route("/update-profile", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        return redirect("/login.html")

    user_id = session["user_id"]

    name = request.form["name"]
    last_name = request.form["last_name"]
    email = request.form["email"]

    conn = get_connection()
    cursor = conn.cursor()

    # 🔥 actualizar datos
    cursor.execute("""
        UPDATE users
        SET name=%s, last_name=%s, email=%s
        WHERE id=%s
    """, (name, last_name, email, user_id))

    conn.commit()

    # 🔥 actualizar sesión también
    session["name"] = name

    conn.close()

    flash("Perfil actualizado correctamente ✅", "success")

    return redirect("/profile.html")

    # =========================
    # 📸 SUBIDA DE IMAGEN
    # =========================
    
@app.route("/update-avatar", methods=["POST"])
def update_avatar():
    if "user_id" not in session:
        return redirect("/login.html")

    user_id = session["user_id"]

    image = request.files.get("profile_image")

    if image and image.filename != "":
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image.save(image_path)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users SET profile_image=%s WHERE id=%s
        """, (filename, user_id))

        conn.commit()
        conn.close()

    flash("Perfil actualizado correctamente ✅", "success")
    return redirect("/profile.html")

@app.route("/delete-account", methods=["POST"])
def delete_account():
    if "user_id" not in session:
        return redirect("/login.html")

    user_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    # borrar relaciones primero (IMPORTANTE)
    cursor.execute("DELETE FROM applications WHERE user_id=%s", (user_id,))
    cursor.execute("DELETE FROM favorites WHERE user_id=%s", (user_id,))
    cursor.execute("DELETE FROM jobs WHERE user_id=%s", (user_id,))

    # borrar usuario
    cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))

    conn.commit()
    conn.close()

    session.clear()

    return redirect("/")

@app.route("/change-password", methods=["POST"])
def change_password():
    if "user_id" not in session:
        return redirect("/login.html")

    user_id = session["user_id"]

    current_password = request.form["current_password"]
    new_password = request.form["new_password"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT password FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()

    if user["password"] != current_password:
        conn.close()
        flash("Contraseña incorrecta ❌", "error")
        return redirect("/profile.html")

    cursor.execute("""
        UPDATE users SET password=%s WHERE id=%s
    """, (new_password, user_id))

    conn.commit()
    conn.close()

    flash("Contraseña actualizada correctamente🔐","success")
    return redirect("/profile.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# =========================
# JOBS PAGE
# =========================
@app.route("/jobs")
def jobs():
    if "user_id" not in session:
        return redirect("/login.html")

    user_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # 🔥 MIS TRABAJOS
    cursor.execute("SELECT * FROM jobs WHERE user_id=%s", (user_id,))
    my_jobs = cursor.fetchall()

    # 🔥 TRABAJOS APLICADOS
    cursor.execute("""
        SELECT jobs.*
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        WHERE applications.user_id = %s
    """, (user_id,))
    applied_jobs = cursor.fetchall()

    conn.close()

    return render_template("jobs.html", my_jobs=my_jobs, applied_jobs=applied_jobs)

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

# ==================================
# PANEL DE EMPRESAS, CREAR TRABAJOS 
# ==================================
@app.route("/create-job", methods=["POST"])
def create_job():
    if "user_id" not in session:
        return redirect("/login.html")

    title = request.form["title"]
    description = request.form["description"]
    salary = request.form["salary"]
    location = request.form["location"]
    user_id = session["user_id"]  # 🔥 IMPORTANTE
    company = request.form["company"]
    job_type = request.form["job_type"]
    requirements = request.form["requirements"]
    benefits = request.form["benefits"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO jobs 
    (title, description, salary, location, user_id, company, job_type, requirements, benefits)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (title, description, salary, location, user_id, company, job_type, requirements, benefits))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/create-job-page")
def create_job_page():
    if "user_id" not in session:
        return redirect("/login.html")

    return render_template("create-job.html")

# =========================
# BORRAR TRABJOS
# =========================
@app.route("/delete-job/<int:id>", methods=["POST"])
def delete_job(id):
    if "user_id" not in session:
        return redirect("/login.html")

    user_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    # 🔐 Solo elimina si es tuyo
    cursor.execute(
        "DELETE FROM jobs WHERE id=%s AND user_id=%s",
        (id, user_id)
    )

    conn.commit()
    conn.close()

    return redirect("/jobs")

# =========================
# MIS TRABAJOS
# =========================
@app.route("/my-jobs")
def my_jobs():
    if "user_id" not in session:
        return redirect("/login.html")

    user_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM jobs WHERE user_id=%s", (user_id,))
    jobs = cursor.fetchall()

    conn.close()

    return render_template("my-jobs.html", jobs=jobs)

# =========================
# EDITOR DEL CARDS
# =========================
@app.route("/edit-job/<int:id>")
def edit_job_page(id):
    if "user_id" not in session:
        return redirect("/login.html")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM jobs WHERE id=%s AND user_id=%s",(id, session["user_id"]))
    job = cursor.fetchone()

    conn.close()

    return render_template("edit-job.html", job=job)

# =========================
# ACTUALIZAR CARDS
# =========================
@app.route("/update-job/<int:id>", methods=["POST"])
def update_job(id):
    if "user_id" not in session:
        return redirect("/login.html")

    user_id = session["user_id"]

    title = request.form["title"]
    description = request.form["description"]
    salary = request.form["salary"]
    location = request.form["location"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE jobs
        SET title=%s, description=%s, salary=%s, location=%s
        WHERE id=%s AND user_id=%s
    """, (title, description, salary, location, id, user_id))

    conn.commit()
    conn.close()

    return redirect("/my-jobs")

# =========================
# APARTADO DE FAVIRITOS
# =========================
@app.route("/favorite/<int:job_id>", methods=["POST"])
def add_favorite(job_id):
    if "user_id" not in session:
        return redirect("/login.html")

    user_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    # evitar duplicados
    cursor.execute(
        "SELECT * FROM favorites WHERE user_id=%s AND job_id=%s",
        (user_id, job_id)
    )
    if cursor.fetchone():
        conn.close()
        return redirect("/")

    cursor.execute(
        "INSERT INTO favorites (user_id, job_id) VALUES (%s, %s)",
        (user_id, job_id)
    )

    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# PAGINA DE FAVORITOS
# =========================
@app.route("/favorites")
def favorites_page():
    if "user_id" not in session:
        return redirect("/login.html")

    user_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT jobs.*
        FROM favorites
        JOIN jobs ON favorites.job_id = jobs.id
        WHERE favorites.user_id = %s
    """, (user_id,))

    favorite_jobs = cursor.fetchall()
    conn.close()

    return render_template("favorites.html", jobs=favorite_jobs)

# =========================
# QUITAR FAVORITO
# =========================
@app.route("/unfavorite/<int:job_id>", methods=["POST"])
def remove_favorite(job_id):
    if "user_id" not in session:
        return redirect("/login.html")

    user_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM favorites WHERE user_id=%s AND job_id=%s",
        (user_id, job_id)
    )

    conn.commit()
    conn.close()

    return redirect("/")

# =========================
# DASHBOARD (PROTEGIDO)
# =========================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login.html")

    return render_template("profile.html")  # o dashboard.html

# =========================
# CARGA CURICULUMS
# =========================
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/cv/<filename>")
def view_cv(filename):
    return send_from_directory(
        os.path.join("uploads", "cvs"),
        filename
    )

@app.route("/delete-cv", methods=["POST"])
def delete_cv():

    if "user_id" not in session:
        return redirect("/login.html")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # obtener nombre del cv
    cursor.execute(
        "SELECT cv FROM users WHERE id=%s",
        (session["user_id"],)
    )

    user = cursor.fetchone()

    if user and user["cv"]:
        cv_path = os.path.join("uploads/cv", user["cv"])

        # eliminar archivo físico
        if os.path.exists(cv_path):
            os.remove(cv_path)

        # borrar referencia en DB
        cursor.execute(
            "UPDATE users SET cv=NULL WHERE id=%s",
            (session["user_id"],)
        )

        conn.commit()

    conn.close()

    flash("Curriculum eliminado correctamente", "success")

    return redirect("/profile.html")

@app.route("/upload-cv", methods=["POST"])
def upload_cv():

    if "user_id" not in session:
        return redirect("/login.html")

    cv = request.files.get("cv")

    if not cv:
        return "No se subió archivo"

    if not cv.filename.lower().endswith(".pdf"):
        return "Solo PDFs"

    upload_folder = os.path.join("uploads", "cvs")

    os.makedirs(upload_folder, exist_ok=True)

    import uuid

    filename = f"{uuid.uuid4()}_{secure_filename(cv.filename)}"

    path = os.path.join(upload_folder, filename)

    cv.save(path)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET cv=%s WHERE id=%s",
        (filename, session["user_id"])
    )

    conn.commit()
    conn.close()

    flash("CV subido correctamente", "success")

    return redirect("/profile.html")


# =========================
#  APLICATIONS
# =========================
@app.route("/applications/<int:job_id>")
def view_applications(job_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            applications.id,
            users.name,
            users.email,
            applications.cv
        FROM applications
        JOIN users
            ON applications.user_id = users.id
        WHERE applications.job_id = %s
    """, (job_id,))

    applications = cursor.fetchall()

    conn.close()

    return render_template(
        "applications.html",
        applications=applications
    )

# =========================
# BOTON (POSTULARSE)
# =========================

@app.route("/apply/<int:job_id>", methods=["POST"])
def apply(job_id):

    if "user_id" not in session:
        return redirect("/login.html")

    user_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    # evitar duplicados
    cursor.execute(
        "SELECT * FROM applications WHERE user_id=%s AND job_id=%s",
        (user_id, job_id)
    )

    if cursor.fetchone():
        flash("Ya aplicaste a este trabajo", "error")
        return redirect("/")

    # verificar trabajo
    cursor.execute(
        "SELECT user_id FROM jobs WHERE id=%s",
        (job_id,)
    )

    job = cursor.fetchone()

    if job["user_id"] == user_id:
        flash("No puedes postularte a tu propio trabajo", "error")
        return redirect("/")

    # insertar postulación
    cursor.execute(
        "INSERT INTO applications (user_id, job_id) VALUES (%s, %s)",
        (user_id, job_id)
    )

    cursor.execute("""
    SELECT
    applications.id,
    users.username,
    users.email,
    users.cv
    FROM applications
    JOIN users
    ON applications.user_id = users.id
    WHERE applications.job_id=%s
    """, (job_id,))

    conn.commit()
    conn.close()

    flash("Postulación enviada correctamente", "success")

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)