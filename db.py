import psycopg2
import json
import re
import os

def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            dbname=os.getenv("DB_NAME"),
            port=os.getenv("DB_PORT", 5432)
        )
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def fetch_user_emails_from_db(user_email: str):
    """Fetches all emails linked to a user based on their email address."""
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
        SELECT e.emailid, e.sender, e.header, e.body
        FROM emails e
        JOIN sessions s ON e.emailid = s.emailid
        JOIN users u ON s.userid = u.userid
        WHERE u.email = %s;
    """
    cur.execute(query, (user_email,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"emailid": r[0], "sender": r[1], "header": r[2], "body": r[3]}
        for r in rows
    ]

def write_parsed_email_to_db(emailid: int, parsed_data: dict):
    """Stores parsed invitation data into a JSONB column (for now we can reuse sessions.user_preferences)."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # For demo, just write into sessions.user_preferences JSONB
        query = """
            UPDATE sessions
            SET user_preferences = user_preferences || %s::jsonb
            WHERE emailid = %s;
        """
        cur.execute(query, (json.dumps(parsed_data), emailid))
        conn.commit()
        print(f"✅ Parsed data written for email ID {emailid}")
    except Exception as e:
        print("❌ Failed to write parsed email data:", e)
    finally:
        cur.close()
        conn.close()
