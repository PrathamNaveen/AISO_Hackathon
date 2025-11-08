from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
# from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
import os
import random

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


def fetch_flight_data(preferences: dict):
    """Simulates fetching flight data from an API or DB."""
    print("✈️ Fetching flight data...")
    dummy_flights = [
        {"airline": "Emirates", "price": 480, "duration": "10h", "route": "DXB → AMS"},
        {"airline": "Qatar Airways", "price": 450, "duration": "11h", "route": "DOH → AMS"},
        {"airline": "Lufthansa", "price": 520, "duration": "9h", "route": "FRA → AMS"},
        {"airline": "KLM", "price": 550, "duration": "8h", "route": "DEL → AMS"},
    ]
    flights = [f for f in dummy_flights if f["price"] <= preferences.get("budget", 9999)]
    return sorted(flights, key=lambda f: f["price"])[:3]


# -------------------------------
# LangGraph Nodes
# -------------------------------

llm = ChatOpenAI(model="gpt-5", temperature=0.3)

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
    flights = fetch_flight_data(combined_info)
    return {"flights": flights}


def compute_best_flight(state):
    best = random.choice(state["flights"]) if state.get("flights") else None
    return {"best_flight": best}


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
