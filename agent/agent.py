from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from dotenv import load_dotenv
import os
import sys
import json
import re
from langgraph.checkpoint.memory import InMemorySaver  
from langchain_core.runnables import RunnableConfig
from langgraph.store.memory import InMemoryStore  

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fetch_flight_data import fetch_flight_data_from_api
from message import fetch_flight_data_from_serpapi

# -------------------------------
# Load environment
# -------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print("🔑 OpenAI API Key Loaded:", bool(OPENAI_API_KEY))

# -------------------------------
# Dummy / Helper functions
# -------------------------------


def fetch_flight_data_wrapper(preferences: dict):
    """Fetches flight data and filters it"""
    print("✈️ Fetching flight data...")
    from datetime import datetime, timedelta

    departure_id = preferences.get("departure_airport", "AMS")
    arrival_id = preferences.get("arrival_airport", "ATL")
    outbound_date = preferences.get("date", "2025-12-25")
    days = preferences.get("days", 10)
    currency = preferences.get("currency", "USD")
    budget = preferences.get("budget", 9999)

    # Calculate return date
    try:
        return_date = (datetime.strptime(outbound_date, '%Y-%m-%d') + timedelta(days=days)).strftime('%Y-%m-%d')
    except:
        return_date = "2026-01-04"

    all_flights = fetch_flight_data_from_serpapi(
        departure_id=departure_id,
        arrival_id=arrival_id,
        outbound_date=outbound_date,
        return_date=return_date,
        currency=currency,
        sort_by=1,
        parse_only_essentials=True
    )

    filtered_flights = [f for f in all_flights if f.get("price", float('inf')) <= budget]
    return sorted(filtered_flights, key=lambda f: f["price"])

# -------------------------------
# LangGraph State
# -------------------------------
class MessagesState(TypedDict):
    messages: list[HumanMessage]
    preferences_text: str
    flights: list[dict]
    best_flight: dict
    user_choice: str

llm = ChatOpenAI(model="gpt-5", temperature=0.3,
                 base_url="https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1")

# -------------------------------
# Node Definitions
# -------------------------------
def start_node(state: MessagesState):
    print("👋 Welcome! Let's find you the best flights.")
    return {"messages": [HumanMessage(content="Hi! I can help you find flights. Where are you flying from and to?")]}

def get_user_preferences(state: MessagesState):
    user_input = input("✈️ Enter your travel preferences (e.g., 'Delhi to Amsterdam next week, budget $500'): ")
    preferences_dict = {"preferences_text": str(user_input)}
    chain.update_state(config, preferences_dict, as_node="ask_preferences")
    return preferences_dict

def flight_data_node(state: MessagesState):
    user_text = state.get("preferences_text", "")
    combined_info = {"user_query": user_text}
    try:
        flights = fetch_flight_data_wrapper(combined_info)
    except Exception as e:
        print(f"❌ Error fetching flight data: {e}")
        flights = []
    flights_dict = {"flights": flights}
    chain.update_state(config, flights_dict, as_node="fetch_flight")
    return flights_dict

def compute_best_flight(state: MessagesState):
    flights = state.get("flights", [])
    if not flights:
        best_flight_dict = {"best_flight": None}
        chain.update_state(config, best_flight_dict, as_node="compute_best_flight")
        return best_flight_dict

    user_prefs = state.get("preferences_text", "")

    flights_text = "\n".join([
        f"{i+1}. Airline: {f.get('airline', 'N/A')}, Price: ${f.get('price', 'N/A')}, Duration: {f.get('duration', 'N/A')}, Route: {f.get('route', 'N/A')}"
        for i, f in enumerate(flights)
    ])

    prompt = f"""
You are a travel assistant. Pick the three best flight option based on user preferences and available flights. It should be three json objects.

User preferences: {user_prefs}

Available flights:
{flights_text}

Return ONLY valid JSON (no markdown) with this exact structure:
{{
    "airline": "<airline_name>",
    "price": <price_in_number>,
    "duration": "<duration>",
    "route": "<route>",
    "reason": "<why this flight is best for the user>"
}}
"""
    try:
        response = llm.invoke([HumanMessage(content=prompt)]).content
        cleaned = re.sub(r'```json\s*|\s*```', '', response).strip()
        best_flight = json.loads(cleaned)
        print(f"✅ Best flight: {best_flight}")
    except Exception as e:
        print(f"❌ LLM failed or JSON error: {e}")
        best_flight = sorted(flights, key=lambda f: f.get("price", float('inf')))[0]
        best_flight["reason"] = "Fallback: Cheapest option"

    best_flight_dict = {"best_flight": best_flight}
    chain.update_state(config, best_flight_dict, as_node="compute_best_flight")
    return best_flight_dict

def display_flights(state: MessagesState):
    flights = state.get("flights", [])
    if not flights:
        return {"user_choice": "no"}

    print("\n🧾 Top available flights:")
    for i, f in enumerate(flights, start=1):
        print(f"{i}. {f['airline']} - ${f['price']} - {f['duration']} - {f['route']}")
    choice = input("\nWould you like to book one of these? (yes/no): ").strip().lower()
    return {"user_choice": choice}

def booking_or_repeat(state: MessagesState):
    if state.get("user_choice") == "yes":
        print("✅ Proceeding with the booking process...")
        return {"status": "booking_confirmed"}
    else:
        print("🔁 Let's refine your search.")
        return {"status": "loop_back"}

# -------------------------------
# Graph Setup
# -------------------------------
workflow = StateGraph(MessagesState)
workflow.add_node("start", start_node)
workflow.add_node("ask_preferences", get_user_preferences)
workflow.add_node("fetch_flight", flight_data_node)
workflow.add_node("compute_best_flight", compute_best_flight)
workflow.add_node("display", display_flights)
workflow.add_node("decision", booking_or_repeat)

workflow.add_edge(START, "start")
workflow.add_edge("start", "ask_preferences")
workflow.add_edge("ask_preferences", "fetch_flight")


workflow.add_edge("fetch_flight", "compute_best_flight")
workflow.add_edge("compute_best_flight", "display")
workflow.add_edge("display", "decision")
workflow.add_conditional_edges("decision", lambda s: "ask_preferences" if s.get("status")=="loop_back" else END)

# -------------------------------
# Compile & Run
# -------------------------------
checkpointer = InMemorySaver()
store = InMemoryStore()
chain = workflow.compile(checkpointer=checkpointer, store=store)
config: RunnableConfig = {"configurable": {"thread_id": "1"}}

if __name__ == "__main__":
    print("🚀 Starting Flight Finder Agent...\n")
    final_state = chain.invoke({}, config=config)
    print("\n🏁 Final state:", final_state)
