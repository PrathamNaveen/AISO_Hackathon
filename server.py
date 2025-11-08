from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from importlib import import_module
import traceback

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

