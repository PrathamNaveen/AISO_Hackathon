# server.py
from fastapi import FastAPI, HTTPException, Depends, Cookie, Response, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr,ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import jwt
import os
import json

from db import get_db_connection
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Flight Assistant API",
    description="Minimal AI-powered flight booking assistant",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Config
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

# -----------------------
# Models
# -----------------------

class SignupRequest(BaseModel):
    email: EmailStr
    name: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AirportLocation(BaseModel):
    code: str
    label: Optional[str] = None

class StayRange(BaseModel):
    minDays: int
    maxDays: int

class ArriveBeforeDays(BaseModel):
    min: int
    max: int

class EventResponse(BaseModel):
    id: str
    title: str
    location: str
    start: str
    organizer: str
    rawEmailId: str
    processed: bool = False

from pydantic import BaseModel, ConfigDict

class EssentialInfoResponse(BaseModel):
    meetingId: str
    from_location: AirportLocation
    to_location: AirportLocation
    travel_class: str = "economy"
    tripType: str = "round-trip"
    stayRange: StayRange
    arriveBeforeDays: ArriveBeforeDays

    model_config = ConfigDict(from_attributes=True, alias_generator=lambda s: {"from_location": "from", "to_location": "to"}.get(s, s))


class EssentialInfoRequest(BaseModel):
    from_location: AirportLocation
    to_location: AirportLocation
    travel_class: str = "economy"
    tripType: str = "round-trip"
    stayRange: StayRange
    arriveBeforeDays: ArriveBeforeDays

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda s: {"from_location": "from", "to_location": "to"}.get(s, s)
    )

class ConfirmResponse(BaseModel):
    taskId: str
    meetingId: str
    status: str = "accepted"
    message: str = "Agent planning started"

class ReasoningLog(BaseModel):
    ts: str
    type: str
    text: str
    meta: Optional[Dict[str, Any]] = {}

class ReasoningResponse(BaseModel):
    meetingId: str
    log: List[ReasoningLog]

class FlightCandidate(BaseModel):
    id: str
    price: float
    itinerary: str
    provider: str
    duration: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None

class FlightSearchRequest(BaseModel):
    meetingId: str
    departure: str
    arrival: str
    date: str
    returnDate: Optional[str] = None
    travel_class: str = "economy"
    budget: Optional[float] = None

class FlightSearchResponse(BaseModel):
    searchId: str
    status: str
    candidates: List[FlightCandidate]

class BookingResponse(BaseModel):
    bookingId: str
    status: str
    confirmationNumber: str
    itinerary: Dict[str, Any]

# -----------------------
# JWT Utils
# -----------------------
def create_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(session_token: Optional[str] = Cookie(None)) -> dict:
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_token(session_token)
    return {"user_id": int(payload["sub"]), "email": payload["email"]}

# -----------------------
# DB Helpers
# -----------------------
def get_user_by_email(email: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT userid, email, name FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if user:
            return {"userid": user[0], "email": user[1], "name": user[2]}
        return None
    finally:
        cur.close()
        conn.close()

def create_user(email: str, name: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (email, name, password) VALUES (%s, %s, %s) RETURNING userid",
            (email, name, "temp")
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id
    finally:
        cur.close()
        conn.close()

def get_events_for_user(user_id: int) -> List[Dict]:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT emailid, header, body, sender
            FROM emails
            ORDER BY emailid DESC
        """)
        events = []
        for row in cur.fetchall():
            events.append({
                "id": f"evt_{row[0]}",
                "title": row[1] or "Untitled Meeting",
                "location": extract_location(row[2] or ""),
                "start": datetime.utcnow().isoformat() + "Z",
                "organizer": row[3],
                "rawEmailId": f"gmail_msg_{row[0]}",
                "processed": False
            })
        return events
    finally:
        cur.close()
        conn.close()

def extract_location(text: str) -> str:
    cities = ["amsterdam", "new york", "london", "paris", "tokyo", "delhi", "atlanta"]
    text_lower = text.lower()
    for c in cities:
        if c in text_lower:
            return c.title()
    return "Unknown"

def save_session(user_id: int, prefs: dict) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO sessions (userid, user_preferences)
            VALUES (%s, %s::jsonb)
            RETURNING sessionid
        """, (user_id, json.dumps(prefs)))
        session_id = cur.fetchone()[0]
        conn.commit()
        return session_id
    finally:
        cur.close()
        conn.close()

def save_flight_booking(user_id: int, flight_data: dict) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO flights (userid, departure, arrival, currency, price, airline)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING flightid
        """, (
            user_id,
            flight_data.get("departure"),
            flight_data.get("arrival"),
            flight_data.get("currency", "USD"),
            flight_data.get("price"),
            flight_data.get("airline")
        ))
        flight_id = cur.fetchone()[0]
        conn.commit()
        return flight_id
    finally:
        cur.close()
        conn.close()

def get_user_by_email(email: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT userid, email, name, password FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        if row:
            return {"userid": row[0], "email": row[1], "name": row[2], "password": row[3]}
        return None
    finally:
        cur.close()
        conn.close()

def create_user(email: str, name: str, password: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (email, name, password) VALUES (%s, %s, %s) RETURNING userid",
            (email, name, password)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id
    finally:
        cur.close()
        conn.close()


# -----------------------
# Routes
# -----------------------
@app.post("/api/auth/signup")
def signup(req: SignupRequest, response: Response):
    existing_user = get_user_by_email(req.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    user_id = create_user(req.email, req.name, req.password)
    token = create_token(user_id, req.email)
    response.set_cookie("session_token", token, httponly=True, max_age=TOKEN_EXPIRE_HOURS*3600, samesite="lax")
    return {"message": "Signup successful", "user": {"userid": user_id, "email": req.email, "name": req.name}}

@app.post("/api/auth/login")
def login(req: LoginRequest, response: Response):
    user = get_user_by_email(req.email)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user["userid"], user["email"])
    response.set_cookie("session_token", token, httponly=True, max_age=TOKEN_EXPIRE_HOURS*3600, samesite="lax")
    return {"message": "Login successful", "user": {"userid": user["userid"], "email": user["email"], "name": user["name"]}}

@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("session_token")
    return {"message": "Logged out"}

@app.get("/api/events", response_model=List[EventResponse])
def list_events(current_user: dict = Depends(get_current_user)):
    return get_events_for_user(current_user["user_id"])

@app.get("/api/meetings/{meeting_id}/essential", response_model=EssentialInfoResponse)
def get_essential_info(meeting_id: str, current_user: dict = Depends(get_current_user)):
    return EssentialInfoResponse(
        meetingId=meeting_id,
        from_location=AirportLocation(code="JFK", label="John F. Kennedy (JFK)"),
        to_location=AirportLocation(code="AMS", label="Amsterdam (AMS)"),
        travel_class="business",
        tripType="round-trip",
        stayRange=StayRange(minDays=2, maxDays=5),
        arriveBeforeDays=ArriveBeforeDays(min=0, max=1)
    )

@app.post("/api/meetings/{meeting_id}/essential/confirm", response_model=ConfirmResponse, status_code=202)
def confirm_essential_info(meeting_id: str, info: EssentialInfoRequest, current_user: dict = Depends(get_current_user)):
    prefs = {
        "from": info.from_location.code,
        "to": info.to_location.code,
        "class": info.travel_class,
        "tripType": info.tripType,
        "stayRange": info.stayRange.dict(),
        "arriveBeforeDays": info.arriveBeforeDays.dict()
    }
    session_id = save_session(current_user["user_id"], prefs)
    task_id = f"agent_task_{session_id}"
    return ConfirmResponse(taskId=task_id, meetingId=meeting_id)

@app.get("/api/agent/reasoning/{meeting_id}", response_model=ReasoningResponse)
def get_reasoning(meeting_id: str, current_user: dict = Depends(get_current_user)):
    log = [
        ReasoningLog(ts=datetime.utcnow().isoformat()+"Z", type="step", text="Prefill origin detected: JFK", meta={"confidence": 0.92}),
        ReasoningLog(ts=(datetime.utcnow()+timedelta(seconds=70)).isoformat()+"Z", type="stage", text="Searching flights")
    ]
    return ReasoningResponse(meetingId=meeting_id, log=log)

@app.post("/api/flights/search", response_model=FlightSearchResponse)
def search_flights(search: FlightSearchRequest, current_user: dict = Depends(get_current_user)):
    # Mock flights for demo
    candidates = [
        FlightCandidate(id="f_1", price=1450.0, itinerary=f"{search.departure}->{search.arrival} 1 stop", provider="AirX"),
        FlightCandidate(id="f_2", price=1520.0, itinerary=f"{search.departure}->{search.arrival} Non-stop", provider="FlyFast")
    ]
    search_id = f"s_{int(datetime.utcnow().timestamp())}"
    return FlightSearchResponse(searchId=search_id, status="completed", candidates=candidates)

@app.post("/api/flights/book")
def book_flight(flight_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    flight_id = save_flight_booking(current_user["user_id"], flight_data)
    return {"bookingId": f"b_{flight_id}", "status": "pending", "message": "Booking initiated"}

@app.get("/api/bookings/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: str, current_user: dict = Depends(get_current_user)):
    flight_id = int(booking_id.replace("b_", ""))
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT flightid, departure, arrival, price, airline, currency FROM flights WHERE flightid=%s AND userid=%s", (flight_id, current_user["user_id"]))
        flight = cur.fetchone()
        if not flight:
            raise HTTPException(status_code=404, detail="Booking not found")
        return BookingResponse(
            bookingId=booking_id,
            status="confirmed",
            confirmationNumber=f"CONF{flight[0]:06d}",
            itinerary={
                "departure": flight[1],
                "arrival": flight[2],
                "price": float(flight[3]),
                "airline": flight[4],
                "currency": flight[5]
            }
        )
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
