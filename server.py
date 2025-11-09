# server.py
from fastapi import FastAPI, HTTPException, Depends, Cookie, Response, Path, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from importlib import import_module
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import traceback
import uuid
from pathlib import Path
from typing import Tuple
from db import fetch_parsed_invitations_from_db

from db import get_db_connection
from dotenv import load_dotenv
from agent import run_flight_finder_agent_with_preferences


app = FastAPI()

# Enable CORS for local frontend development. In prod, lock this down to your
# real frontend origin or use an nginx reverse-proxy so services are same-origin.
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Preferences(BaseModel):
    departure_airport: Optional[str] = Field(None, description="IATA code of departure airport")
    arrival_airport: Optional[str] = Field(None, description="IATA code of arrival airport")
    date: Optional[str] = Field(None, description="Outbound date YYYY-MM-DD")
    days: Optional[int] = Field(7, description="Trip length in days")
    currency: Optional[str] = Field("USD")
    budget: Optional[float] = Field(None)
    # allow extra arbitrary fields
    extra: Optional[Dict[str, Any]] = None


class FlightCandidate(BaseModel):
    id: Optional[str]
    airline: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    duration: Optional[str]
    route: Optional[str]
    details: Optional[Dict[str, Any]] = None


class BookingRequest(BaseModel):
    meeting_id: Optional[str]
    candidate_id: str
    user_info: Optional[Dict[str, Any]] = None


@app.get("/")
def read_root():
    return {"message": "Hello, AISO!"}


def _lazy_import_agent():
    """Lazy import of the agent module. Returns module or raises ImportError.

    We import at request time so server import doesn't fail if agent's dependencies
    are missing in this environment. The caller should catch ImportError and
    return a 500 with the traceback for debugging.
    """
    try:
        agent = import_module("agent.agent")
        return agent
    except Exception:
        raise


# ----------------------------
# Simple in-memory mock datastore
# ----------------------------
def _rand(prefix: str = '') -> str:
    return prefix + uuid.uuid4().hex[:8]


_mock = {
    "events": [
        {
            "id": "evt_1",
            "title": "AI - AISO Meetup",
            "location": "Amsterdam",
            "start": None,
            "organizer": "bob@company.com",
            "rawEmailId": "gmail_msg_abc",
            "processed": False,
        },
        {
            "id": "evt_2",
            "title": "Sales Offsite",
            "location": "New York",
            "start": None,
            "organizer": "sarah@company.com",
            "rawEmailId": "gmail_msg_def",
            "processed": False,
        },
    ],
    
    "short_term": {
        "essential": {
            "meetingId": "evt_1",
            "from": {"code": "JFK", "label": "John F. Kennedy (JFK)"},
            "to": {"code": "AMS", "label": "Amsterdam (AMS)"},
            "class": "business",
            "tripType": "round-trip",
            "stayRange": {"minDays": 2, "maxDays": 5},
            "arriveBeforeDays": {"min": 0, "max": 1},
    },
    },
    "searches": {},
    "bookings": {},
}


def _load_json_if_exists(name: str) -> Tuple[bool, list]:
    p = Path(name)
    if p.exists():
        try:
            return True, json.loads(p.read_text())
        except Exception:
            return False, []
    return False, []


# try to load parsed flights as fallback data
_, PARSED_FLIGHTS = _load_json_if_exists("parsed_flights.json")
_, TOP_3_FLIGHTS = _load_json_if_exists("top_3_flights.json")


@app.post("/api/agent/search_flights", response_model=List[FlightCandidate])
def search_flights(prefs: Preferences):
    """Search flights using the logic in `agent.py`.

    This calls `fetch_flight_data_wrapper(preferences_dict)` from `agent.py`.
    """
    try:
        agent = _lazy_import_agent()
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail={"error": "Failed to import agent module", "trace": tb})

    # Prefer a dedicated wrapper function if present
    if hasattr(agent, "fetch_flight_data_wrapper"):
        try:
            prefs_dict = prefs.dict()
            # merge extras if provided
            if prefs.extra:
                prefs_dict.update(prefs.extra)
            flights = agent.fetch_flight_data_wrapper(prefs_dict)
            # Normalize/validate to FlightCandidate list
            out = []
            for f in flights or []:
                out.append(FlightCandidate(**{k: v for k, v in f.items()}))
            return out
        except Exception:
            tb = traceback.format_exc()
            raise HTTPException(status_code=500, detail={"error": "Agent execution failed", "trace": tb})
    else:
        raise HTTPException(status_code=501, detail="Agent does not expose fetch_flight_data_wrapper")


# ----------------------------
# Frontend-facing mock endpoints
# ----------------------------


@app.get("/api/events")
def get_events():
    return _mock["events"]


@app.get("/api/meetings/{meeting_id}/essential")
def get_essential():
    essential = _mock.get("short_term", {}).get("essential")
    if not essential:
        raise HTTPException(status_code=404, detail="essential info not set")
    return essential
    


@app.post("/api/meetings/{meeting_id}/essential/confirm", status_code=202)
def confirm_essential(meeting_id: str, payload: Dict[str, Any], background_tasks: BackgroundTasks):
    _mock.setdefault("short_term", {})["essential"] = payload

    # produce a task id to indicate the action was accepted (no background work here)
    task_id = _rand("task_")
    return {"taskId": task_id, "meetingId": meeting_id, "status": "accepted", "message": "Essential info updated"}

@app.get("/api/invitations")
def get_invitations(user_id: str):
    """
    Fetch all parsed invitations for a given user from the database.
    """
    try:
        invitations = fetch_parsed_invitations_from_db(user_id)
        # Transform to frontend-friendly structure
        formatted = [
            {
                "id": inv.get("emailid"),
                "title": inv.get("header"),
                "location": inv.get("location", "Amsterdam"),
                "start": inv.get("event_time", ""),
            }
            for inv in invitations
        ]
        return formatted
    except Exception as e:
        return {"error": str(e)}

class UserPreferences(BaseModel):
    departure_airport: str
    arrival_airport: str
    date: str
    days: int = 10
    currency: str = "USD"
    budget: float = 9999


@app.post("/api/preferences")
async def set_user_preferences(preferences: UserPreferences):
    try:
        pref_dict = preferences.dict()
        result = run_flight_finder_agent_with_preferences(pref_dict)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/flights/search")
def flights_search(body: Dict[str, Any]):
    """Search flights. Try to call agent.fetch_flight_data_wrapper if available,
    otherwise return a mock FlightSearchResponse.
    """
    # try agent first
    try:
        agent = _lazy_import_agent()
    except Exception:
        agent = None

    if agent and hasattr(agent, "fetch_flight_data_wrapper"):
        try:
            prefs = body or {}
            flights = agent.fetch_flight_data_wrapper(prefs)
            # build response
            sid = _rand("s_")
            candidates = []
            for i, f in enumerate(flights or []):
                candidates.append({
                    "id": f.get("id") or f"f_{i}",
                    "price": f.get("price"),
                    "itinerary": f.get("route"),
                    "provider": f.get("airline") or f.get("provider"),
                    "details": f,
                })
            resp = {"searchId": sid, "status": "completed", "candidates": candidates}
            _mock["searches"][sid] = resp
            return resp
        except Exception:
            tb = traceback.format_exc()
            raise HTTPException(status_code=500, detail={"error": "agent search failed", "trace": tb})

    # fallback to local parsed/top_3 data
    candidates = []
    for i, f in enumerate((PARSED_FLIGHTS or TOP_3_FLIGHTS)[:5]):
        candidates.append({
            "id": f.get("airline", "f") + f"_{i}",
            "price": f.get("price"),
            "itinerary": f.get("route"),
            "provider": f.get("airline"),
            "details": f,
        })
    sid = _rand("s_")
    resp = {"searchId": sid, "status": "completed", "candidates": candidates}
    _mock["searches"][sid] = resp
    return resp


@app.get("/api/agent/reasoning/{meeting_id}")
def get_reasoning(meeting_id: str):
    # TODO: recieve the result from the getflight, get the reason part
    log = _mock["reasoning"].get(meeting_id, [])
    return {"meetingId": meeting_id, "log": log}


@app.get("/api/bookings/{booking_id}")
def get_booking(booking_id: str):
    if booking_id in _mock["bookings"]:
        return _mock["bookings"][booking_id]
    raise HTTPException(status_code=404, detail="booking not found")


@app.post("/api/bookings")
def post_booking(body: Dict[str, Any]):
    # body may contain candidate_id, meeting_id, user_info
    candidate_id = body.get("candidate_id") or body.get("candidateId")
    meeting_id = body.get("meeting_id") or body.get("meetingId")
    b_id = _rand("b_")
    confirmation = _rand("C-")
    booking = {"bookingId": b_id, "status": "confirmed", "confirmationNumber": confirmation, "itinerary": {"candidate_id": candidate_id}, "meeting_id": meeting_id}
    _mock["bookings"][b_id] = booking
    return booking



@app.post("/api/agent/rag")
def rag_lookup(payload: Dict[str, Any]):
    """Call agent.fetch_from_rag to get RAG hints for a query. Expects {'query': '...'}"""
    try:
        agent = _lazy_import_agent()
    except Exception:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail={"error": "Failed to import agent module", "trace": tb})

    if hasattr(agent, "fetch_from_rag"):
        try:
            q = payload.get("query") if isinstance(payload, dict) else None
            return agent.fetch_from_rag(q or "")
        except Exception:
            tb = traceback.format_exc()
            raise HTTPException(status_code=500, detail={"error": "RAG failed", "trace": tb})
    else:
        raise HTTPException(status_code=501, detail="Agent does not expose fetch_from_rag")


@app.post("/api/agent/book")
def create_booking(req: BookingRequest):
    """Placeholder booking endpoint.

    The agent/booking flow is application-specific. This endpoint simply echoes
    a confirmation and would be the place to insert DB persistence or calls to
    downstream booking/procurement services.
    """
    # In a real app you'd persist booking and return the record ID.
    return {
        "status": "ok",
        "booking_id": f"bk_{req.candidate_id}_{req.meeting_id or 'nomtg'}",
        "candidate_id": req.candidate_id,
        "meeting_id": req.meeting_id,
        "user_info": req.user_info,
    }
  
  
class SignupRequest(BaseModel):
    email: EmailStr
    name: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def get_user_by_email(email: str = 'dummy@gmail.com'):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        print("Fetching user by email:", email)
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

@app.post("/api/auth/signup")
def signup(req: SignupRequest, response: Response):
    existing_user = get_user_by_email(req.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    user_id = create_user(req.email, req.name, req.password)
    return {"message": "Signup successful", "user": {"userid": user_id, "email": req.email, "name": req.name}}

@app.post("/api/auth/login")
def login(req: LoginRequest, response: Response):
    user = get_user_by_email(req.email)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"message": "Login successful", "user": {"userid": user["userid"], "email": user["email"], "name": user["name"]}}
