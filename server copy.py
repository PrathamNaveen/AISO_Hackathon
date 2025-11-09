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

from db import get_db_connection
from dotenv import load_dotenv

app = FastAPI()

# Enable CORS for local frontend development. In prod, lock this down to your
# real frontend origin or use an nginx reverse-proxy so services are same-origin.
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

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
    "essential": {
        "evt_1": {
            "meetingId": "evt_1",
            "from": {"code": "JFK", "label": "John F. Kennedy (JFK)"},
            "to": {"code": "AMS", "label": "Amsterdam (AMS)"},
            "class": "business",
            "tripType": "round-trip",
            "stayRange": {"minDays": 2, "maxDays": 5},
            "arriveBeforeDays": {"min": 0, "max": 1},
        }
    },
    "short_term": {},
    "reasoning": {
        "evt_1": [
            {"ts": "2025-11-09T00:00:00Z", "type": "step", "text": "Prefill origin detected: JFK", "meta": {"confidence": 0.92}}
        ]
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

# fake
@app.get("/api/events")
def get_events():
    return _mock["events"]

# fake
@app.get("/api/meetings/{meeting_id}/essential")
def get_essential(meeting_id: str):
    # prefer short-term override then essential prefill
    if meeting_id in _mock["short_term"]:
        return _mock["short_term"][meeting_id]
    if meeting_id in _mock["essential"]:
        return _mock["essential"][meeting_id]
    # fallback empty structure
    return {
        "meetingId": meeting_id,
        "from": {"code": "AMS", "label": "Amsterdam (AMS)"},
        "to": {"code": "JFK", "label": "John F. Kennedy (JFK)"},
        "class": "economy",
        "tripType": "round-trip",
        "stayRange": {"minDays": 2, "maxDays": 7},
        "arriveBeforeDays": {"min": 0, "max": 1},
    }


@app.post("/api/meetings/{meeting_id}/essential/confirm", status_code=202)
def confirm_essential(meeting_id: str, payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """Accepts a partial EssentialInfo payload, stores it in short-term memory and
    triggers a mock background search task (synchronous here but returns a task id).
    """
    # save short-term memory
    _mock["short_term"][meeting_id] = payload

    # create a mock search task
    task_id = _rand("task_")

    # create candidate search result now (in real app this would be async)
    candidates = []
    if PARSED_FLIGHTS:
        # take top N from parsed flights as mock candidates
        for i, f in enumerate(PARSED_FLIGHTS[:3]):
            candidates.append({
                "id": f.get("airline", "f") + f"_{i}",
                "price": f.get("price"),
                "itinerary": f.get("route"),
                "provider": f.get("airline"),
                "details": f,
            })
    elif TOP_3_FLIGHTS:
        for i, f in enumerate(TOP_3_FLIGHTS[:3]):
            candidates.append({
                "id": f"f_{i}",
                "price": f.get("price"),
                "itinerary": f.get("route"),
                "provider": f.get("airline"),
                "details": f,
            })
    else:
        # very small deterministic fallback
        candidates = [
            {"id": _rand("f_"), "price": 999, "itinerary": "AMS → JFK non-stop", "provider": "MockAir", "details": {}},
            {"id": _rand("f_"), "price": 1299, "itinerary": "AMS → JFK 1 stop", "provider": "MockAir", "details": {}},
        ]

    search_id = _rand("s_")
    _mock["searches"][search_id] = {"searchId": search_id, "status": "completed", "candidates": candidates}

    return {"taskId": search_id, "status": "queued"}


# ...existing code...
@app.post("/api/flights/search")
def flights_search(body: Dict[str, Any]):
    """Search flights. Use agent workflow nodes if available:
       - ask_preferences / get_user_preferences
       - flight_data_node or fetch_flight_data_wrapper
       - compute_best_flight
    Returns agent-driven response when possible; falls back to local data otherwise.
    Response contains diagnostic fields: usedAgent (bool) and fallbackReason (str) for testing.
    """
    prefs = body or {}
    # Try to import agent
    try:
        agent = _lazy_import_agent()
    except Exception as e:
        agent = None
        import_tb = traceback.format_exc()

    # If agent is present, attempt to run nodes in sequence
    if agent:
        try:
            # 1) Ask preferences / normalize preferences
            if hasattr(agent, "ask_preferences"):
                try:
                    user_prefs = agent.ask_preferences(prefs)
                except Exception:
                    user_prefs = prefs
            elif hasattr(agent, "get_user_preferences"):
                try:
                    user_prefs = agent.get_user_preferences(prefs)
                except Exception:
                    user_prefs = prefs
            else:
                user_prefs = prefs

            # 2) Fetch flight data via node or wrapper
            flights = None
            if hasattr(agent, "flight_data_node"):
                try:
                    flights = agent.flight_data_node(user_prefs)
                except Exception:
                    flights = None
            if not flights and hasattr(agent, "fetch_flight_data_wrapper"):
                try:
                    flights = agent.fetch_flight_data_wrapper(user_prefs)
                except Exception:
                    flights = None

            # Normalize flights into list of dicts
            flights = flights or []

            # 3) Compute best/ranked flights
            agent_result = None
            if hasattr(agent, "compute_best_flight"):
                try:
                    state = {"flights": flights, "preferences": user_prefs}
                    agent_result = agent.compute_best_flight(state)
                except Exception:
                    agent_result = None

            # Build candidates list from flights
            candidates = []
            for i, f in enumerate(flights or []):
                # Accept dict-like or objects with attributes
                try:
                    fd = dict(f) if isinstance(f, dict) else f.__dict__
                except Exception:
                    fd = f if isinstance(f, dict) else {}
                candidates.append({
                    "id": fd.get("id") or fd.get("airline", "f") + f"_{i}",
                    "price": fd.get("price"),
                    "itinerary": fd.get("route") or fd.get("itinerary"),
                    "provider": fd.get("airline") or fd.get("provider"),
                    "details": fd,
                })

            sid = _rand("s_")
            resp = {"searchId": sid, "status": "completed", "candidates": candidates}

            # Attach agent result if present (best / ranked / raw)
            if agent_result:
                # Normalize expected shapes
                if isinstance(agent_result, dict) and ("best_flight" in agent_result or "ranked" in agent_result):
                    resp["agent"] = agent_result
                    if "best_flight" in agent_result:
                        resp["best"] = agent_result["best_flight"]
                    if "ranked" in agent_result:
                        resp["ranked"] = agent_result["ranked"]
                else:
                    # sometimes compute_best_flight returns a list or raw text
                    resp["agent"] = {"raw": agent_result}

            resp["usedAgent"] = True
            _mock["searches"][sid] = resp
            return resp

        except Exception:
            tb = traceback.format_exc()
            # If you want "strict agent only" behavior, raise here instead of falling back.
            # For debugging include the traceback in the fallback reason.
            fallback_reason = f"Agent execution failed: {str(e)}. Trace:\n{tb}"
            # continue to fallback below
    else:
        import_tb = import_tb if 'import_tb' in locals() else "agent import not attempted"

    # --- Fallback to local parsed/top_3 data ---
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
    resp["usedAgent"] = False
    # include diagnostic info so frontend/dev can tell this was fallback
    resp["fallbackReason"] = fallback_reason if 'fallback_reason' in locals() else ("agent import failed:\n" + (import_tb if 'import_tb' in locals() else "unknown"))
    _mock["searches"][sid] = resp
    return resp
# ...existing code...


@app.get("/api/agent/reasoning/{meeting_id}")
def get_reasoning(meeting_id: str):
    """Return reasoning for a meeting.

    Behaviour:
    - If the agent module is available and exposes helper functions, call into the
      agent to compute a best-flight + reasoning (best-effort). We seed the agent
      with any short-term memory or essential info we have for the meeting.
    - On any failure or if the agent isn't available, return the in-memory mock
      reasoning so the frontend still works.
    """
    # seed preferences from short-term memory or essential prefill
    prefs = {}
    if meeting_id in _mock["short_term"]:
        prefs = _mock["short_term"][meeting_id]
    elif meeting_id in _mock["essential"]:
        prefs = _mock["essential"][meeting_id]

    try:
        agent = _lazy_import_agent()
    except Exception:
        # agent not importable; return mock reasoning
        log = _mock["reasoning"].get(meeting_id, [])
        return {"meetingId": meeting_id, "log": log}

    # If agent provides a compute_best_flight helper and a flight fetcher, use them
    try:
        flights = None
        if hasattr(agent, "fetch_flight_data_wrapper"):
            try:
                flights = agent.fetch_flight_data_wrapper(prefs or {})
            except Exception:
                flights = None

        reasoning_entry = None
        # Prefer a single-step compute_best_flight function if available
        if hasattr(agent, "compute_best_flight"):
            try:
                state = {"flights": flights or [], "rag_data": {}, "preferences_text": prefs.get("notes", "") if isinstance(prefs, dict) else ""}
                res = agent.compute_best_flight(state)
                best = res.get("best_flight") if isinstance(res, dict) else None
                if best:
                    text = best.get("reason") or (best.get("airline") and f"Chose {best.get('airline')} @ {best.get('price')}")
                    reasoning_entry = {"ts": datetime.utcnow().isoformat() + "Z", "type": "agent", "text": text, "meta": {"best": best}}
            except Exception:
                reasoning_entry = None

        # If we have agent reasoning, return it
        if reasoning_entry:
            return {"meetingId": meeting_id, "log": [reasoning_entry], "best": reasoning_entry["meta"]["best"]}

    except Exception:
        # fall through to returning mock
        pass

    # fallback
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

# @app.post("/api/auth/signup")
# def signup(req: SignupRequest, response: Response):
#     existing_user = get_user_by_email(req.email)
#     if existing_user:
#         raise HTTPException(status_code=400, detail="User with this email already exists")
    
#     user_id = create_user(req.email, req.name, req.password)
#     token = create_token(user_id, req.email)
#     response.set_cookie("session_token", token, httponly=True, max_age=TOKEN_EXPIRE_HOURS*3600, samesite="lax")
#     return {"message": "Signup successful", "user": {"userid": user_id, "email": req.email, "name": req.name}}

# @app.post("/api/auth/login")
# def login(req: LoginRequest, response: Response):
#     user = get_user_by_email(req.email)
#     if not user or user["password"] != req.password:
#         raise HTTPException(status_code=401, detail="Invalid email or password")

#     token = create_token(user["userid"], user["email"])
#     response.set_cookie("session_token", token, httponly=True, max_age=TOKEN_EXPIRE_HOURS*3600, samesite="lax")
#     return {"message": "Login successful", "user": {"userid": user["userid"], "email": user["email"], "name": user["name"]}}

