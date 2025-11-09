from db import write_parsed_email_to_db
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Optional
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
from filter_calender import get_december_2025_events, filter_flights as filter_flights_against_calendar

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
    """
    Fetches flight data, merges user preferences with defaults,
    filters based on all criteria, and returns matching flights.
    """
    print("✈️ Fetching and filtering flight data...")

    from datetime import datetime, timedelta

    # ---- Default preferences ----
    default_preferences = {
        "departure_airport": "BUD",
        "arrival_airport": "LIN",
        "date": "2025-12-25",
        "days": 10,
        "currency": "USD",
        "budget": 9999,
        "outbound_date": "2025-12-25"
    }

    # ---- Merge user preferences ----
    merged = {**default_preferences, **(preferences or {})}

    # Convert date properly
    try:
        outbound_date = merged.get("date") or merged.get("outbound_date")
        outbound_dt = datetime.strptime(outbound_date, "%Y-%m-%d")
        return_date = (outbound_dt + timedelta(days=int(merged.get("days", 10)))).strftime("%Y-%m-%d")
    except Exception:
        print("⚠️ Invalid or missing date in preferences, using default 2025-12-25")
        outbound_dt = datetime(2025, 12, 25)
        return_date = (outbound_dt + timedelta(days=10)).strftime("%Y-%m-%d")

    # Extract core preferences
    departure_id = merged.get("departure_airport")
    arrival_id = merged.get("arrival_airport")
    currency = merged.get("currency")
    budget = merged.get("budget", 9999)

    # ---- Fetch all available flights ----
    try:
        all_flights = fetch_flight_data_from_serpapi(
            departure_id=departure_id,
            arrival_id=arrival_id,
            outbound_date=outbound_dt.strftime("%Y-%m-%d"),
            return_date=return_date,
            currency=currency,
            sort_by=1,
            parse_only_essentials=True
        )
    except Exception as e:
        print(f"❌ Flight data fetch failed: {e}")
        return []

    if not all_flights:
        print("📭 No flights fetched from API.")
        return []

    # ---- Filter flights based on preferences ----
    filtered_flights = []
    for f in all_flights:
        try:
            # Core validations
            if f.get("departure") and f["departure"].upper() != departure_id.upper():
                continue
            if f.get("arrival") and f["arrival"].upper() != arrival_id.upper():
                continue

            # Budget filter
            if f.get("price") and float(f["price"]) > float(budget):
                continue

            # Optional: date window filter
            flight_date = f.get("departure_date") or f.get("date")
            if flight_date:
                try:
                    fdate = datetime.strptime(flight_date.split("T")[0], "%Y-%m-%d")
                    if fdate < outbound_dt or fdate > outbound_dt + timedelta(days=int(merged["days"])):
                        continue
                except:
                    pass  # skip malformed dates

            filtered_flights.append(f)
        except Exception as inner_err:
            print(f"⚠️ Error filtering a flight: {inner_err}")

    # ---- Handle case: no suitable flights ----
    if not filtered_flights:
        print("😔 No suitable flights found matching your preferences.")
        return [{"message": "No suitable flights found for your preferences."}]

    # ---- Sort & return ----
    sorted_flights = sorted(filtered_flights, key=lambda f: f.get("price", float('inf')))
    print(f"✅ Found {len(sorted_flights)} suitable flights.")
    return sorted_flights

# -------------------------------
# LangGraph State
# -------------------------------
class MessagesState(TypedDict):
    messages: list[HumanMessage]
    preferences_text: str
    flights: list[dict]
    best_flight: dict
    user_choice: str
    calendar_events: Optional[list[dict]]

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

def parse_user_emails_node(state: MessagesState):
    """
    Fetches emails for a user, checks if any are invitations,
    parses them using LLM, writes structured info to the DB,
    and returns all parsed invitations for frontend use.
    """
    try:
        from db import fetch_user_emails_from_db
        from db import write_parsed_email_to_db
    except Exception as e:
        print(f"❌ Failed to import DB functions: {e}")
        return {"parsed_invitations": []}

    try:
        user_email = input("📧 Enter your signed-in email: ").strip()
        if not user_email:
            print("⚠️ No email entered. Skipping email parsing.")
            return {"parsed_invitations": []}

        # Fetch emails from DB
        try:
            emails = fetch_user_emails_from_db(user_email)
        except Exception as db_error:
            print(f"❌ Database fetch error: {db_error}")
            return {"parsed_invitations": []}

        if not emails:
            print("📭 No emails found for this user.")
            return {"parsed_invitations": []}

        print(f"📬 Found {len(emails)} emails. Checking for invitations...")

        parsed_invitations = []
        emails_to_check = emails[:5]  # limit processing

        for email in emails_to_check:
            try:
                text = f"{email.get('header', '')} {email.get('body', '')}".lower()

                # Detect invitation-type emails
                if any(word in text for word in ["invite", "invitation", "meeting", "event", "conference"]):
                    print(f"\n📨 Invitation found: {email.get('header', 'No Subject')}")
                    prompt = f"""
Extract event details from this invitation email.
Email content:
{email.get('header', '')} - {email.get('body', '')}
Return valid JSON only in this format:
{{
  "event_title": "<title>",
  "event_location": "<location or city if mentioned>",
  "event_time": "<time/date if available>"
}}
"""
                    try:
                        response = llm.invoke([HumanMessage(content=prompt)]).content
                        cleaned = re.sub(r'```json\s*|\s*```', '', response).strip()
                        parsed = json.loads(cleaned)

                        # Add emailid reference and save to DB
                        parsed["emailid"] = email.get("emailid")
                        write_parsed_email_to_db(email.get("emailid"), parsed)

                        parsed_invitations.append(parsed)
                        print(f"✅ Parsed and stored event: {parsed}")

                    except json.JSONDecodeError:
                        print("⚠️ LLM returned invalid JSON, skipping this email.")
                    except Exception as e:
                        print(f"⚠️ Error while parsing/writing email {email.get('emailid')}: {e}")
                else:
                    print(f"📨 Skipping non-invitation email: {email.get('header', 'No Subject')}")
            except Exception as inner_err:
                print(f"⚠️ Error while processing an email: {inner_err}")

        print(f"✅ Checked {len(emails)} emails. Found {len(parsed_invitations)} invitations.")
        for invitation in parsed_invitations[:2]:
            print(f"✅ Parsed invitation: {invitation}")
        # Return the structured parsed invitations list
        return {"parsed_invitations": parsed_invitations}

    except Exception as e:
        print(f"💥 Unexpected error in parse_user_emails_node: {e}")
        return {"parsed_invitations": []}



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


def filter_flights_by_calender_node(state: MessagesState):
    flights = state.get("flights", [])

    if not flights:
        print("📭 No flights available for calendar filtering.")
        return {"flights": flights}

    try:
        events = get_december_2025_events()
    except Exception as e:
        print(f"⚠️ Failed to fetch calendar events: {e}")
        return {"flights": flights}

    if not events:
        print("📭 No calendar events found; skipping calendar-based filtering.")
        result_state = {"flights": flights, "calendar_events": []}
        chain.update_state(config, result_state, as_node="filter_flights_by_calender")
        return result_state

    try:
        filtered_flights = filter_flights_against_calendar(events, flights)
    except Exception as e:
        print(f"⚠️ Calendar filtering failed: {e}")
        filtered_flights = flights

    if not filtered_flights:
        print("😕 Calendar filtering removed all flights. Keeping original list.")
        filtered_flights = flights
    else:
        print(f"🗓️ {len(filtered_flights)} flights remain after calendar filtering.")

    result_state = {"flights": filtered_flights, "calendar_events": events}
    chain.update_state(config, result_state, as_node="filter_flights_by_calender")
    return result_state

def compute_best_flight(state: MessagesState):
    flights = state.get("flights", [])
    if not flights:
        best_flight_dict = {"best_flight": []}
        chain.update_state(config, best_flight_dict, as_node="compute_best_flight")
        return best_flight_dict

    user_prefs = state.get("preferences_text", "")

    flights_text = "\n".join([
        f"{i+1}. Airline: {f.get('airline', 'N/A')}, Price: ${f.get('price', 'N/A')}, Duration: {f.get('duration', 'N/A')}, Route: {f.get('route', 'N/A')}"
        for i, f in enumerate(flights)
    ])

    prompt = f"""
You are a travel assistant. Pick the three best flight options based on user preferences and available flights.
Only choose flights that fit the user's given preferences (departure, arrival, dates, and budget). 
Avoid unnecessary or irrelevant results.

User preferences:
{user_prefs}

Available flights:
{flights_text}

Return ONLY valid JSON (no markdown) with this exact structure:
[
  {{
    "airline": "<airline_name>",
    "price": <price_in_number>,
    "duration": "<duration>",
    "route": "<route>",
    "reason": "<why this flight is best for the user>"
  }},
  {{
    "airline": "<airline_name>",
    "price": <price_in_number>,
    "duration": "<duration>",
    "route": "<route>",
    "reason": "<why this flight is best for the user>"
  }},
  {{
    "airline": "<airline_name>",
    "price": <price_in_number>,
    "duration": "<duration>",
    "route": "<route>",
    "reason": "<why this flight is best for the user>"
  }}
]
"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)]).content
        cleaned = re.sub(r'```json\s*|\s*```', '', response).strip()
        best_flights = json.loads(cleaned)

        # Ensure it's always a list (LLM safety)
        if isinstance(best_flights, dict):
            best_flights = [best_flights]
        elif not isinstance(best_flights, list):
            raise ValueError("Unexpected JSON format returned from LLM")

        print(f"✅ Best 3 flights found:")
        for i, f in enumerate(best_flights, start=1):
            print(f"  {i}. {f.get('airline', 'N/A')} - ${f.get('price', 'N/A')} - {f.get('duration', 'N/A')} - {f.get('route', 'N/A')}")

    except Exception as e:
        print(f"❌ LLM failed or JSON error: {e}")
        # Fallback: pick top 3 cheapest flights
        sorted_flights = sorted(flights, key=lambda f: f.get("price", float('inf')))
        best_flights = sorted_flights[:3]
        for f in best_flights:
            f["reason"] = "Fallback: Cheapest available option"

    best_flight_dict = {"best_flight": best_flights}
    chain.update_state(config, best_flight_dict, as_node="compute_best_flight")
    return best_flight_dict

def display_flights(state: MessagesState):
    best_flights = state.get("best_flight", [])
    if not best_flights:
        print("😕 No best flights available to display.")
        return {"user_choice": "no"}

    print("\n🏆 Top 3 flight recommendations:")
    for i, f in enumerate(best_flights, start=1):
        print(f"\n{i}. ✈️ {f.get('airline', 'N/A')}")
        print(f"   💰 Price: ${f.get('price', 'N/A')}")
        print(f"   🕒 Duration: {f.get('duration', 'N/A')}")
        print(f"   🧭 Route: {f.get('route', 'N/A')}")
        print(f"   💬 Reason: {f.get('reason', 'N/A')}")

    choice = input("\nWould you like to book one of these flights? (yes/no): ").strip().lower()
    return {"user_choice": choice}


def booking_or_repeat(state: MessagesState):
    """Handles user's decision to book or refine search."""
    choice = state.get("user_choice", "").lower()
    best_flight = state.get("best_flight")

    if choice == "yes":
        # Handle both list and dict best_flight structures
        if isinstance(best_flight, list) and len(best_flight) > 0:
            chosen = best_flight[0]
        elif isinstance(best_flight, dict):
            chosen = best_flight
        else:
            print("⚠️ No valid flight found.")
            return {"status": "loop_back"}

        # Print details cleanly
        print("\n🛫 Booking your flight...")
        print(f"✈️ Airline: {chosen.get('airline', 'Unknown')}")
        print(f"💰 Price: ${chosen.get('price', 'N/A')}")
        print(f"🕒 Duration: {chosen.get('duration', 'N/A')}")
        print(f"🧭 Route: {chosen.get('route', 'N/A')}")
        print(f"💬 Reason: {chosen.get('reason', 'N/A')}")
        print("✅ Booking confirmed! Have a great trip! 🌍\n")

        return {"status": "booking_confirmed"}

    else:
        print("\n🔁 Okay, let’s refine your search preferences.\n")
        return {"status": "loop_back"}


# -------------------------------
# Graph Setup
# -------------------------------
workflow = StateGraph(MessagesState)
workflow.add_node("start", start_node)
workflow.add_node("parse_emails", parse_user_emails_node)
workflow.add_node("ask_preferences", get_user_preferences)
workflow.add_node("fetch_flight", flight_data_node)
workflow.add_node("filter_flights_by_calender", filter_flights_by_calender_node)
workflow.add_node("compute_best_flight", compute_best_flight)
workflow.add_node("display", display_flights)
workflow.add_node("decision", booking_or_repeat)

workflow.add_edge(START, "parse_emails")
# workflow.add_edge(, "parse_emails")
workflow.add_edge("parse_emails", "ask_preferences")
workflow.add_edge("ask_preferences", "fetch_flight")
workflow.add_edge("fetch_flight", "filter_flights_by_calender")
workflow.add_edge("filter_flights_by_calender", "compute_best_flight")
workflow.add_edge("compute_best_flight", "display")
workflow.add_edge("display", "decision")
workflow.add_conditional_edges(
    "decision",
    lambda s: "ask_preferences" if s.get("status") == "loop_back" else END,
)
# -------------------------------
# Compile & Run
# -------------------------------
checkpointer = InMemorySaver()
store = InMemoryStore()
chain = workflow.compile(checkpointer=checkpointer, store=store)
config: RunnableConfig = {"configurable": {"thread_id": "1"}}

def run_flight_finder_agent(config: RunnableConfig = {"configurable": {"thread_id": "1"}}):
    """
    Runs the full flight finder graph and returns final results.
    Useful for running on servers or from other scripts.
    """
    print("🚀 Starting Flight Finder Agent...\n")
    final_state = chain.invoke({}, config=config)

    status = final_state.get("status")
    best_flight = final_state.get("best_flight")

    # Return structured data (not just print)
    if status == "booking_confirmed" and best_flight:
        result = {
            "status": "booking_confirmed",
            "best_flight": best_flight
        }
    else:
        result = {
            "status": status or "incomplete",
            "best_flight": None
        }

    print("🏁 Agent finished execution.")
    return result

def generate_reasoning_from_state(state: MessagesState):
    """
    Takes the current workflow state and asks the LLM to output stepwise reasoning
    explaining why the selected flights are the best options.
    """
    best_flights = state.get("best_flight", [])
    user_prefs = state.get("preferences_text", "")
    all_flights = state.get("flights", [])

    if not best_flights or not all_flights:
        return {"reasoning_steps": ["No flights available to generate reasoning."]}

    flights_text = "\n".join([
        f"{i+1}. Airline: {f.get('airline', 'N/A')}, Price: ${f.get('price', 'N/A')}, Duration: {f.get('duration', 'N/A')}, Route: {f.get('route', 'N/A')}"
        for i, f in enumerate(all_flights)
    ])

    best_flights_text = "\n".join([
        f"{i+1}. Airline: {f.get('airline', 'N/A')}, Price: ${f.get('price', 'N/A')}, Duration: {f.get('duration', 'N/A')}, Route: {f.get('route', 'N/A')}"
        for i, f in enumerate(best_flights)
    ])

    prompt = f"""
You are a travel assistant. The user preferences are:
{user_prefs}

All available flights:
{flights_text}

The selected top flights are:
{best_flights_text}

Explain, step by step, why each of the selected flights is the best choice for the user.
Return a JSON object with this structure:
{{
  "reasoning_steps": [
    "<Stepwise reasoning 1>",
    "<Stepwise reasoning 2>",
    "<Stepwise reasoning 3>"
  ]
}}
"""
    try:
        response = llm.invoke([HumanMessage(content=prompt)]).content
        cleaned = re.sub(r'```json\s*|\s*```', '', response).strip()
        reasoning_json = json.loads(cleaned)
        return reasoning_json
    except Exception as e:
        print(f"❌ LLM reasoning generation failed: {e}")
        return {"reasoning_steps": ["Could not generate reasoning."]}


if __name__ == "__main__":
    print("🚀 Starting Flight Finder Agent...\n")
    final_state = chain.invoke({}, config=config)
    reasoning = generate_reasoning_from_state(final_state)
