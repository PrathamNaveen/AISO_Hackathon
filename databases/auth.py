import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from .db import get_db_connection


def init_auth_db():
    """Create users and sessions tables if they don't exist."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                userid SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(150) UNIQUE NOT NULL,
                bookings INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS sessions (
                sessionid SERIAL PRIMARY KEY,
                userid INTEGER REFERENCES users(userid) ON DELETE CASCADE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                expires_at TIMESTAMP WITH TIME ZONE
            );
            """
        )
        conn.commit()
        # Ensure compatibility with other schemas: if sessions table already exists
        # without an expires_at column (older schema), add it now and backfill
        try:
            cur.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITH TIME ZONE;")
            # backfill from session_duration if present
            cur.execute(
                """
                DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='sessions' AND column_name='session_duration') THEN
                        UPDATE sessions SET expires_at = now() + session_duration WHERE expires_at IS NULL AND session_duration IS NOT NULL;
                    END IF;
                END$$;
                """
            )
            conn.commit()
        except Exception:
            # non-fatal; leave as-is and let runtime operations handle schema differences
            conn.rollback()
    finally:
        cur.close()
        conn.close()


def create_user(name: str, email: str, password: str) -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s,%s,%s) RETURNING userid,name,email", (name, email, password))
        user = cur.fetchone()
        conn.commit()
        return dict(user)
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return {}
    finally:
        cur.close()
        conn.close()


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT userid,name,email FROM users WHERE email=%s AND password=%s", (email, password))
        user = cur.fetchone()
        return dict(user) if user else None
    finally:
        cur.close()
        conn.close()


def create_session(userid: int, duration_minutes: int = 60) -> int:
    expires = datetime.utcnow() + timedelta(minutes=duration_minutes)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO sessions (userid, expires_at) VALUES (%s,%s) RETURNING sessionid", (userid, expires))
        sid = cur.fetchone()[0]
        conn.commit()
        return sid
    finally:
        cur.close()
        conn.close()


def get_user_by_session(sessionid: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT u.userid,u.name,u.email,s.expires_at FROM sessions s JOIN users u ON s.userid = u.userid WHERE s.sessionid = %s",
            (sessionid,)
        )
        row = cur.fetchone()
        if not row:
            return None
        # check expiry
        if row.get("expires_at") and row["expires_at"] < datetime.utcnow():
            # session expired: delete it
            cur2 = conn.cursor()
            cur2.execute("DELETE FROM sessions WHERE sessionid=%s", (sessionid,))
            conn.commit()
            cur2.close()
            return None
        return dict(row)
    finally:
        cur.close()
        conn.close()


def delete_session(sessionid: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM sessions WHERE sessionid=%s", (sessionid,))
        conn.commit()
    finally:
        cur.close()
        conn.close()
