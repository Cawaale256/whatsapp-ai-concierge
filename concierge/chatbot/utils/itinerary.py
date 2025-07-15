import re
from dateparser.search import search_dates
import spacy

nlp = spacy.load("en_core_web_sm")

def extract_itinerary_info(user_message):
    lowered = user_message.lower()

    # Step 1: Extract up to 2 dates from natural language
    found_dates = search_dates(user_message)
    parsed_dates = sorted([dt.date() for _, dt in found_dates]) if found_dates else []
    start_date = parsed_dates[0] if len(parsed_dates) > 0 else None
    end_date = parsed_dates[1] if len(parsed_dates) > 1 else None

    # Step 2: Detect destination using NER (Geo-political Entity)
    destination = None
    doc = nlp(user_message)
    for ent in doc.ents:
        if ent.label_ == "GPE":
            destination = ent.text.title()
            break

    # Step 3: Extract Day 1–7+ plans using regex
    day_plan_pattern = re.findall(r"(day\s*(\d+))[^\w]{0,10}([a-z\s]{3,})", lowered)
    daily_plan = {f"Day {int(day_num)}": plan.strip().capitalize() for _, day_num, plan in day_plan_pattern}

    # Step 4: Handle "first day" fallback for Day 1
    if "Day 1" not in daily_plan:
        day1_match = re.search(r"(first day|day one|day 1)[^\w]{0,10}([a-z\s]+)", lowered)
        if day1_match:
            daily_plan["Day 1"] = day1_match.group(2).strip().capitalize()

    print(f"[🧭] Extracted ➜ Destination: {destination}, Dates: {parsed_dates}, Plans: {daily_plan}")

    # Step 5: Always return a safe structure
    return {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "daily_plan": daily_plan
    }
