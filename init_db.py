# init_db.py
import psycopg2
from psycopg2 import sql, extras
import os

# Load environment variables if using .env
from dotenv import load_dotenv
load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "flight_assistant")


def get_connection(dbname="postgres"):
    return psycopg2.connect(
        dbname=dbname,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )


def create_database():
    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
    exists = cur.fetchone()
    if not exists:
        print(f"Creating database {DB_NAME}...")
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
    cur.close()
    conn.close()


def create_tables():
    conn = get_connection(DB_NAME)
    cur = conn.cursor()

    # USERS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        userid SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        password VARCHAR(255) NOT NULL,
        email VARCHAR(150) UNIQUE NOT NULL,
        sessionids INTEGER[],
        flightid INTEGER,
        bookings INTEGER DEFAULT 0
    );
    """)

    # EMAILS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        emailid SERIAL PRIMARY KEY,
        sender VARCHAR(150) NOT NULL,
        header VARCHAR(255),
        body TEXT
    );
    """)

    # SESSIONS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        sessionid SERIAL PRIMARY KEY,
        userid INTEGER REFERENCES users(userid) ON DELETE CASCADE,
        emailid INTEGER REFERENCES emails(emailid) ON DELETE SET NULL,
        session_duration INTERVAL,
        context_window_length INTEGER,
        user_preferences JSONB DEFAULT '{}'
    );
    """)

    # FLIGHTS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS flights (
        flightid SERIAL PRIMARY KEY,
        userid INTEGER REFERENCES users(userid) ON DELETE CASCADE,
        departure VARCHAR(10),
        arrival VARCHAR(10),
        currency VARCHAR(10),
        price NUMERIC(10,2),
        airline VARCHAR(100)
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Tables created successfully.")


def insert_dummy_data():
    conn = get_connection(DB_NAME)
    cur = conn.cursor()

    # Users
    cur.execute("""
    INSERT INTO users (name, password, email, sessionids, bookings)
    VALUES 
    ('Pratham', 'hashed_pwd_123', 'pratham@example.com', ARRAY[1,2], 2)
    ON CONFLICT (email) DO NOTHING;
    """)

    cur.execute("""
    INSERT INTO users (name, password, email, sessionids, bookings)
    VALUES 
    ('Aisha', 'hashed_pwd_456', 'aisha@example.com', ARRAY[3], 1)
    ON CONFLICT (email) DO NOTHING;
    """)

    # Emails
    cur.execute("""
    INSERT INTO emails (sender, header, body)
    VALUES
    ('bot@flightai.com', 'Meeting Invitation - Amsterdam', 'Hey Pratham, join us for a meeting in Amsterdam next week!')
    ON CONFLICT DO NOTHING;
    """)
    cur.execute("""
    INSERT INTO emails (sender, header, body)
    VALUES
    ('bot@flightai.com', 'Meeting Confirmation - Delhi', 'Aisha, your session meeting in Delhi is confirmed.')
    ON CONFLICT DO NOTHING;
    """)

    # Flights
    cur.execute("""
    INSERT INTO flights (userid, departure, arrival, currency, price, airline)
    VALUES
    (1, 'DEL', 'AMS', 'EUR', 480.00, 'KLM Royal Dutch')
    ON CONFLICT DO NOTHING;
    """)
    cur.execute("""
    INSERT INTO flights (userid, departure, arrival, currency, price, airline)
    VALUES
    (1, 'AMS', 'DEL', 'EUR', 470.00, 'Emirates')
    ON CONFLICT DO NOTHING;
    """)
    cur.execute("""
    INSERT INTO flights (userid, departure, arrival, currency, price, airline)
    VALUES
    (2, 'DEL', 'BOM', 'INR', 120.00, 'IndiGo')
    ON CONFLICT DO NOTHING;
    """)

    # Sessions
    cur.execute("""
    INSERT INTO sessions (userid, emailid, session_duration, context_window_length, user_preferences)
    VALUES
    (1, 1, INTERVAL '30 minutes', 5, '{"preferred_airlines": ["KLM", "Emirates"], "budget": 500, "class": "Economy"}')
    ON CONFLICT DO NOTHING;
    """)
    cur.execute("""
    INSERT INTO sessions (userid, emailid, session_duration, context_window_length, user_preferences)
    VALUES
    (1, 1, INTERVAL '45 minutes', 6, '{"preferred_airlines": ["Emirates"], "budget": 600, "class": "Business"}')
    ON CONFLICT DO NOTHING;
    """)
    cur.execute("""
    INSERT INTO sessions (userid, emailid, session_duration, context_window_length, user_preferences)
    VALUES
    (2, 2, INTERVAL '25 minutes', 4, '{"preferred_airlines": ["IndiGo"], "budget": 200, "class": "Economy"}')
    ON CONFLICT DO NOTHING;
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Dummy data inserted successfully.")


if __name__ == "__main__":
    conn = get_connection(DB_NAME)
    cur = conn.cursor()
    create_database()
    create_tables()
    insert_dummy_data()
    print("✅ Database initialization complete!")
    cur.execute("SELECT * FROM emails")
    print(cur.fetchall())
    cur.close()
    conn.close()