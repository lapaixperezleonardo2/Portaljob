import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin",  # ← usa la contraseña correcta
        database="portal_job"
    )