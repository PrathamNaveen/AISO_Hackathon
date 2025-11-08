from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
# from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
import os
import random
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fetch_flight_data import fetch_flight_data_from_api
from message import fetch_flight_data_from_serpapi
import json


# Load environment
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print("🔑 OpenAI API Key Loaded:", bool(OPENAI_API_KEY))

# -------------------------------
# Dummy functions (replace later)
# -------------------------------

def fetch_from_rag(user_query: str):
    """Simulates retrieving relevant data from a RAG system."""
    print("🔍 Fetching info from RAG...")
    # Dummy RAG info
    return {
        "preferred_airlines": ["Emirates", "Qatar Airways"],
        "budget": 500,
        "preferred_class": "Economy"
    }


def fetch_flight_data_wrapper(preferences: dict):
    """Fetches real flight data from SerpAPI using the imported function."""
    print("✈️ Fetching flight data...")
    
    from datetime import datetime, timedelta
    
    # Extract parameters from preferences dict
    departure_id = preferences.get("departure_airport", "AMS")
    arrival_id = preferences.get("arrival_airport", "ATL")
    outbound_date = preferences.get("date", "2025-12-25")
    days = preferences.get("days", 10)
    
    # Calculate return date
    try:
        return_date = (datetime.strptime(outbound_date, '%Y-%m-%d') + 
                      timedelta(days=days)).strftime('%Y-%m-%d')
    except:
        return_date = "2026-01-04"  # fallback
    
    currency = preferences.get("currency", "USD")
    budget = preferences.get("budget", 9999)
    
    # Fetch parsed flight data from SerpAPI
    all_flights = fetch_flight_data_from_serpapi(
        departure_id=departure_id,
        arrival_id=arrival_id,
        outbound_date=outbound_date,
        return_date=return_date,
        currency=currency,
        sort_by=1,
        parse_only_essentials=True
    )
    
    # Filter by budget and return top 3
    filtered_flights = [f for f in all_flights if f["price"] <= budget]
    return sorted(filtered_flights, key=lambda f: f["price"])[:3]


# -------------------------------
# LangGraph Nodes
# -------------------------------

llm = ChatOpenAI(model="gpt-5", temperature=0.3, base_url="https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1")

class MessagesState(TypedDict):
    """State to hold messages and intermediate data."""
    messages: list[HumanMessage]
    preferences_text: str
    rag_data: dict
    flights: list[dict]
    best_flight: dict
    user_choice: str


def start_node(state: MessagesState):
    print("👋 Welcome! Let's find you the best flights.")
    return {
        "messages": [HumanMessage(content="Hi! I can help you find flights. Where are you flying from and to?")]
    }


def get_user_preferences(state: MessagesState):
    user_input = input("✈️ Enter your travel preferences (e.g., 'Delhi to Amsterdam next week, budget $500'): ")
    return {"preferences_text": user_input}


def rag_node(state):
    rag_data = fetch_from_rag(state["preferences_text"])
    return {"rag_data": rag_data}


def flight_data_node(state):
    rag_info = state.get("rag_data", {})
    user_text = state.get("preferences_text", "")
    combined_info = {**rag_info, "user_query": user_text}
    flights = fetch_flight_data_from_serpapi()
    return {"flights": flights}


def compute_best_flight(state):
    """Use LLM to analyze flights and return the best flight with reasoning."""
    flights = state.get("flights", [])
    if not flights:
        print("❌ No flight data found for comparison.")
        return {"best_flight": None}
    
    user_prefs = state.get("preferences_text", "")
    rag_data = state.get("rag_data", {})
    
    # Summarize flights for LLM
    flights_text = "\n".join([
        f"{i+1}. Airline: {f.get('airline', 'N/A')}, "
        f"Price: ${f.get('price', 'N/A')}, "
        f"Duration: {f.get('duration', 'N/A')}, "
        f"Route: {f.get('route', 'N/A')}"
        for i, f in enumerate(flights)
    ])
    
    prompt = f"""
You are a smart travel assistant. Based on the user's preferences and available flights,
pick the single best flight option that fits them best.

User preferences: {user_prefs}
RAG data (preferences): {rag_data}

Available flights:
{flights_text}

Analyze price, airline, duration, and route according to the user's preferences.
Return ONLY valid JSON (no markdown, no extra text) with this exact structure:
{{
    "airline": "<airline_name>",
    "price": <price_in_number>,
    "duration": "<duration>",
    "route": "<route>",
    "reason": "<why this flight is best for the user>"
}}
"""
    
    try:
        # Make LLM call
        response = llm.invoke([HumanMessage(content=prompt)]).content
        print(f"🤖 Raw LLM Response:\n{response}\n")
        
        # Clean response (remove markdown code blocks if present)
        import re
        
        # Remove markdown code blocks
        cleaned = re.sub(r'```json\s*|\s*```', '', response).strip()
        
        # Parse JSON
        best_flight = json.loads(cleaned)
        
        print(f"✅ LLM chose: {best_flight.get('airline', 'Unknown')} (${best_flight.get('price', 'N/A')})")
        print(f"🧠 Reason: {best_flight.get('reason', 'No reason given')}")
        
        return {"best_flight": best_flight}
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Raw LLM Output:\n{response}")
        # Fallback: pick cheapest
        best_flight = sorted(flights, key=lambda f: f.get("price", float('inf')))[0]
        best_flight["reason"] = "Fallback: Cheapest option (LLM parsing failed)"
        return {"best_flight": best_flight}
        
    except Exception as e:
        print(f"❌ Error calling LLM: {type(e).__name__}: {e}")
        
        # Check if it's an auth error
        if "authentication" in str(e).lower() or "api key" in str(e).lower():
            print("🔑 API Key issue detected. Check your OPENAI_API_KEY in .env file")
            print("   Visit: https://platform.openai.com/api-keys")
        
        # Fallback: pick cheapest
        if flights:
            best_flight = sorted(flights, key=lambda f: f.get("price", float('inf')))[0]
            best_flight["reason"] = f"Fallback: Cheapest option (Error: {str(e)[:50]})"
            return {"best_flight": best_flight}
        else:
            return {"best_flight": None}



def display_flights(state):
    flights = state.get("flights", [])
    if not flights:
        print("❌ No flights found. Try again.")
        return {"user_choice": "no"}

    print("\n🧾 Top 3 available flights:")
    for i, f in enumerate(flights, start=1):
        print(f"{i}. {f['airline']} - ${f['price']} - {f['duration']} - {f['route']}")
    choice = input("\nWould you like to book one of these? (yes/no): ").strip().lower()
    return {"user_choice": choice}


def booking_or_repeat(state):
    print(state["user_choice"])
    if state["user_choice"] == "yes":
        print("✅ Proceeding with the booking process...")
        return {"status": "booking_confirmed"}
    else:
        print("🔁 Let's refine your search.")
        return {"status": "loop_back"}


# -------------------------------
# Graph Setup (New API)
# -------------------------------

workflow = StateGraph(MessagesState)

# Define nodes
workflow.add_node("start", start_node)
workflow.add_node("ask_preferences", get_user_preferences)
workflow.add_node("rag", rag_node)
workflow.add_node("fetch_flight", flight_data_node)
workflow.add_node("compute_best_flight", compute_best_flight)
workflow.add_node("display", display_flights)
workflow.add_node("decision", booking_or_repeat)

# Flow control
workflow.add_edge(START, "start")
workflow.add_edge("start", "ask_preferences")

# Conditional edge to RAG
def should_use_rag(state):
    prefs = state.get("preferences_text", "").lower()
    if "recommend" in prefs or "help" in prefs:
        return "rag"
    else:
        return "fetch_flight"

workflow.add_conditional_edges("ask_preferences", should_use_rag)

workflow.add_edge("rag", "fetch_flight")
workflow.add_edge("fetch_flight", "compute_best_flight")
workflow.add_edge("compute_best_flight", "display")
workflow.add_edge("display", "decision")

# Loop back or end
workflow.add_conditional_edges(
    "decision",
    lambda s: "ask_preferences" if s["status"] == "loop_back" else END
)

# -------------------------------
# Compile and Run
# -------------------------------
# memory = InMemorySaver()
# app = workflow.compile(checkpointer=memory)
chain = workflow.compile()


if __name__ == "__main__":
    print("🚀 Starting Flight Finder Agent (LangGraph v0.1+)...\n")
    final_state = chain.invoke({})
    print("\n🏁 Final state:", final_state)
