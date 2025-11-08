import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    print("🔌 Establishing DB connection...")
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT", 5432)
    )
def insert_email(sender, subject, body, received_at):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        query = "INSERT INTO Emails (sender, subject, body, received_at) VALUES (%s, %s, %s, %s)"
        cur.execute(query, (sender, subject, body, received_at))
        conn.commit()
        print(f"✅ Email from {sender} inserted into DB")
    except Exception as e:
        print("❌ DB insert error:", e)
    finally:
        cur.close()
        conn.close()
