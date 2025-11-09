-- ===========================================
-- Flight Assistant Database Setup
-- ===========================================

-- 1️⃣ Create database
-- (Skip this if you already created it via CLI)
CREATE DATABASE flight_assistant;

-- Connect to the database
\c flight_assistant

-- ===========================================
-- 2️⃣ Create Tables
-- ===========================================

-- USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    userid SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    sessionids INTEGER[],  
    flightid INTEGER,
    bookings INTEGER DEFAULT 0
);

-- EMAILS TABLE
CREATE TABLE IF NOT EXISTS emails (
    emailid SERIAL PRIMARY KEY,
    sender VARCHAR(150) NOT NULL,
    header VARCHAR(255),
    body TEXT
);

-- SESSIONS TABLE
CREATE TABLE IF NOT EXISTS sessions (
    sessionid SERIAL PRIMARY KEY,
    userid INTEGER REFERENCES users(userid) ON DELETE CASCADE,
    emailid INTEGER REFERENCES emails(emailid) ON DELETE SET NULL,
    session_duration INTERVAL,
    context_window_length INTEGER,
    user_preferences JSONB DEFAULT '{}'
);

-- FLIGHTS TABLE
CREATE TABLE IF NOT EXISTS flights (
    flightid SERIAL PRIMARY KEY,
    userid INTEGER REFERENCES users(userid) ON DELETE CASCADE,
    departure VARCHAR(10),
    arrival VARCHAR(10),
    currency VARCHAR(10),
    price NUMERIC(10,2),
    airline VARCHAR(100)
);

-- ===========================================
-- 3️⃣ Insert Dummy Data
-- ===========================================

-- Users
INSERT INTO users (name, password, email, sessionids, bookings)
VALUES 
('Pratham', 'hashed_pwd_123', 'pratham@example.com', ARRAY[1,2], 2)
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (name, password, email, sessionids, bookings)
VALUES 
('Aisha', 'hashed_pwd_456', 'aisha@example.com', ARRAY[3], 1)
ON CONFLICT (email) DO NOTHING;

-- Emails
INSERT INTO emails (sender, header, body)
VALUES
('bot@flightai.com', 'Meeting Invitation - Amsterdam', 'Hey Pratham, join us for a meeting in Amsterdam next week!')
ON CONFLICT DO NOTHING;

INSERT INTO emails (sender, header, body)
VALUES
('bot@flightai.com', 'Meeting Confirmation - Delhi', 'Aisha, your session meeting in Delhi is confirmed.')
ON CONFLICT DO NOTHING;

-- Flights
INSERT INTO flights (userid, departure, arrival, currency, price, airline)
VALUES
(1, 'DEL', 'AMS', 'EUR', 480.00, 'KLM Royal Dutch');

INSERT INTO flights (userid, departure, arrival, currency, price, airline)
VALUES
(1, 'AMS', 'DEL', 'EUR', 470.00, 'Emirates');

INSERT INTO flights (userid, departure, arrival, currency, price, airline)
VALUES
(2, 'DEL', 'BOM', 'INR', 120.00, 'IndiGo');

-- Sessions
INSERT INTO sessions (userid, emailid, session_duration, context_window_length, user_preferences)
VALUES
(1, 1, INTERVAL '30 minutes', 5, '{"preferred_airlines": ["KLM", "Emirates"], "budget": 500, "class": "Economy"}');

INSERT INTO sessions (userid, emailid, session_duration, context_window_length, user_preferences)
VALUES
(1, 1, INTERVAL '45 minutes', 6, '{"preferred_airlines": ["Emirates"], "budget": 600, "class": "Business"}');

INSERT INTO sessions (userid, emailid, session_duration, context_window_length, user_preferences)
VALUES
(2, 2, INTERVAL '25 minutes', 4, '{"preferred_airlines": ["IndiGo"], "budget": 200, "class": "Economy"}');

-- ===========================================
-- 4️⃣ Select Queries to Verify
-- ===========================================

-- List all users
SELECT * FROM users;

-- List all emails
SELECT * FROM emails;

-- List all flights
SELECT * FROM flights;

-- List all sessions
SELECT * FROM sessions;

------------------------------------------------------------------------------------------------------------------------------------

-- Join example: user sessions with emails and flights
ALTER TABLE emails
ADD COLUMN is_invitation BOOLEAN DEFAULT FALSE;

-- Example: marking an email as an invitation
UPDATE emails
SET is_invitation = TRUE
WHERE emailid = 3;

SELECT * FROM emails
WHERE is_invitation = TRUE;