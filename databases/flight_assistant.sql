-- ===========================================
-- 🛫 Flight Assistant Database Setup
-- ===========================================

DROP DATABASE IF EXISTS flight_assistant;
CREATE DATABASE flight_assistant;

\c flight_assistant;

-- ===========================================
-- 1️⃣ Create Tables
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
    userid INTEGER REFERENCES users(userid) ON DELETE CASCADE,
    sender VARCHAR(150) NOT NULL,
    header VARCHAR(255),
    body TEXT,
    is_invitation BOOLEAN DEFAULT FALSE
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
-- 2️⃣ Insert Example Users
-- ===========================================

INSERT INTO users (name, password, email, sessionids, bookings)
VALUES 
('Pratham Naveen', 'hashed_pwd_123', 'prathamnaveen.m@gmail.com', ARRAY[1,2], 2),
('Aisha Khan', 'hashed_pwd_456', 'aisha@example.com', ARRAY[3], 1),
('Fly Giraffe Bot', 'hashed_pwd_789', 'bot@flygiraffe.ai', NULL, 0)
ON CONFLICT (email) DO NOTHING;

-- ===========================================
-- 3️⃣ Insert Example Emails
-- ===========================================

INSERT INTO emails (userid, sender, header, body, is_invitation)
VALUES
(1, 'meetings@prosus.com', 'Business Meeting - Amsterdam', 'Hi Pratham, your meeting in Amsterdam is confirmed for next week.', TRUE),
(1, 'events@netapp.com', 'Tech Conference Invite - Berlin', 'Dear Pratham, you’re invited to the AI Tech Conference in Berlin.', TRUE),
(2, 'bot@flightai.com', 'Session Confirmation - Delhi', 'Aisha, your internal meeting in Delhi is confirmed.', TRUE),
(3, 'system@flygiraffe.ai', 'Flight Recommendation Update', 'Your latest flight options are ready.', FALSE);

-- ===========================================
-- 4️⃣ Insert Example Flights
-- ===========================================

INSERT INTO flights (userid, departure, arrival, currency, price, airline)
VALUES
(1, 'DEL', 'AMS', 'EUR', 480.00, 'KLM Royal Dutch'),
(1, 'AMS', 'BER', 'EUR', 150.00, 'EasyJet'),
(2, 'DEL', 'BOM', 'INR', 120.00, 'IndiGo');

-- ===========================================
-- 5️⃣ Insert Example Sessions
-- ===========================================

INSERT INTO sessions (userid, emailid, session_duration, context_window_length, user_preferences)
VALUES
(1, 1, INTERVAL '30 minutes', 5, '{"preferred_airlines": ["KLM", "Emirates"], "budget": 500, "class": "Economy"}'),
(1, 2, INTERVAL '45 minutes', 6, '{"preferred_airlines": ["EasyJet"], "budget": 300, "class": "Economy"}'),
(2, 3, INTERVAL '25 minutes', 4, '{"preferred_airlines": ["IndiGo"], "budget": 200, "class": "Economy"}');

-- ===========================================
-- 6️⃣ Verify Data
-- ===========================================

SELECT * FROM users;
SELECT * FROM emails;
SELECT * FROM flights;
SELECT * FROM sessions;
