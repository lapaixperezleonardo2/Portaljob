from flask import Blueprint, request, redirect, session
from database import get_connection

auth = Blueprint("auth", __name__)

# =========================
# REGISTER
# =========================
@auth.route("/register", methods=["POST"])
def register():

    name = request.form["name"]
    last_name = request.form["last_name"]
    email = request.form["email"]
    password = request.form["password"]
    birth_date = request.form["birth_date"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (name, last_name, email, password, birth_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, last_name, email, password, birth_date))

    conn.commit()

    return redirect("/")


# =========================
# LOGIN
# =========================
@auth.route("/login", methods=["POST"])
def login():

    email = request.form["email"]
    password = request.form["password"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM users 
        WHERE email=%s AND password=%s
    """, (email, password))

    user = cursor.fetchone()

    if user:
        session["user_id"] = user[0]
        session["name"] = user[1]
        return redirect("/dashboard")
    else:
        return "Credenciales incorrectas"


# =========================
# LOGOUT
# =========================
@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")