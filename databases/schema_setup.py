import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def setup_email_database():
    """Creates the database schema for storing emails"""
    
    # Connect to postgres database first
    conn = psycopg2.connect(
        host="localhost",
        user="mihuambra",  # Replace with your Mac username from 'whoami'
        password="",
        dbname="postgres",
        port=5432
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    try:
        # Create database if it doesn't exist
        cur.execute("SELECT 1 FROM pg_database WHERE datname='email_db'")
        if not cur.fetchone():
            cur.execute("CREATE DATABASE email_db")
            print("✅ Database 'email_db' created!")
        else:
            print("ℹ️  Database 'email_db' already exists")
    except Exception as e:
        print(f"❌ Error creating database: {e}")
    finally:
        cur.close()
        conn.close()
    
    # Now connect to gmail_db and create table
    conn = psycopg2.connect(
        host="localhost",
        user="mihuambra",  # Replace with your Mac username
        password="",
        dbname="email_db",
        port=5432
    )
    cur = conn.cursor()
    
    # Create table schema
    create_table_query = """
    CREATE TABLE IF NOT EXISTS emails (
        id SERIAL PRIMARY KEY,
        email_address VARCHAR(255) NOT NULL,
        title TEXT NOT NULL,
        body TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_email_address ON emails(email_address);
    """
    
    try:
        cur.execute(create_table_query)
        conn.commit()
        print("✅ Table 'emails' created successfully!")
        print("\n📋 Schema:")
        print("   - id: auto-incrementing primary key")
        print("   - email_address: sender/recipient email")
        print("   - title: email subject/title")
        print("   - body: email content")
        print("   - created_at: timestamp when inserted")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
    finally:
        cur.close()
        conn.close()


def insert_email(email_address, title, body):
    """Insert an email into the database"""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "mihuambra"),
        password=os.getenv("DB_PASSWORD", ""),
        dbname=os.getenv("DB_NAME", "email_db"),
        port=os.getenv("DB_PORT", 5432)
    )
    cur = conn.cursor()
    
    try:
        query = """
        INSERT INTO emails (email_address, title, body) 
        VALUES (%s, %s, %s)
        """
        cur.execute(query, (email_address, title, body))
        conn.commit()
        print(f"✅ Email from {email_address} inserted into DB")
    except Exception as e:
        print(f"❌ DB insert error: {e}")
    finally:
        cur.close()
        conn.close()


def get_emails_by_address(email_address):
    """Retrieve all emails for a specific email address"""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "mihuambra"),
        password=os.getenv("DB_PASSWORD", ""),
        dbname=os.getenv("DB_NAME", "email_db"),
        port=os.getenv("DB_PORT", 5432)
    )
    cur = conn.cursor()
    
    try:
        query = """
        SELECT id, email_address, title, body, created_at 
        FROM emails 
        WHERE email_address = %s
        ORDER BY created_at DESC
        """
        cur.execute(query, (email_address,))
        results = cur.fetchall()
        return results
    except Exception as e:
        print(f"❌ DB query error: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_all_emails():
    """Retrieve all emails from the database"""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "mihuambra"),
        password=os.getenv("DB_PASSWORD", ""),
        dbname=os.getenv("DB_NAME", "email_db"),
        port=os.getenv("DB_PORT", 5432)
    )
    cur = conn.cursor()
    
    try:
        query = """
        SELECT id, email_address, title, body, created_at 
        FROM emails 
        ORDER BY created_at DESC
        """
        cur.execute(query)
        results = cur.fetchall()
        return results
    except Exception as e:
        print(f"❌ DB query error: {e}")
        return []
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("🚀 Setting up email database...\n")
    
    # Step 1: Setup database and table
    setup_email_database()
    
    print("\n" + "="*50)
    print("📧 Testing with sample data...\n")
    
    # Step 2: Insert some test emails
    insert_email(
        email_address="john@example.com",
        title="Meeting Tomorrow",
        body="Hey, don't forget about our meeting at 3pm tomorrow."
    )
    
    insert_email(
        email_address="jane@example.com",
        title="Project Update",
        body="Here's the latest update on the project status..."
    )
    
    insert_email(
        email_address="john@example.com",
        title="Re: Meeting Tomorrow",
        body="Thanks for the reminder! See you then."
    )
    
    # Step 3: Query emails
    print("\n" + "="*50)
    print("📬 All emails from john@example.com:\n")
    
    johns_emails = get_emails_by_address("john@example.com")
    for email in johns_emails:
        print(f"ID: {email[0]}")
        print(f"From: {email[1]}")
        print(f"Title: {email[2]}")
        print(f"Body: {email[3]}")
        print(f"Date: {email[4]}")
        print("-" * 40)
    
    print("\n" + "="*50)
    print("📬 All emails in database:\n")
    
    all_emails = get_all_emails()
    for email in all_emails:
        print(f"📧 {email[1]} - {email[2]}")
    
    print(f"\n✨ Total emails: {len(all_emails)}")
    print("\n💡 Update your .env file with:")
    print("DB_HOST=localhost")
    print("DB_USER=mihuambra")
    print("DB_PASSWORD=")
    print("DB_NAME=email_db")
    print("DB_PORT=5432")