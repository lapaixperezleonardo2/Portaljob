from database import get_db_connection

def get_all_jobs():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM jobs")
    jobs = cursor.fetchall()
    conn.close()
    return jobs