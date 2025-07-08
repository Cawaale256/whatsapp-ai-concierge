import os
import re
import requests
import string
import spacy
import dateparser
from datetime import date
from dotenv import load_dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from requests.auth import HTTPBasicAuth
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from .models import TravelerProfile, ChatHistory, Itinerary
import dateparser
from dateparser.search import search_dates


# Load environment variables from .env
load_dotenv()

# Load SpaCy model once for destination extraction
nlp = spacy.load("en_core_web_sm")

# Initialize LangChain with GPT-4o
llm = ChatOpenAI(model_name="gpt-4o")

# Healthcheck endpoint
def chatbot_response(request):
    return JsonResponse({"message": "Hello from chatbot_response!"})

# WhatsApp webhook listener
@csrf_exempt
def whatsapp_webhook(request):
    if request.method == "POST":
        try:
            message = request.POST.get("Body", "").strip()
            sender = request.POST.get("From", "").strip()
            if not message:
                return JsonResponse({"status": "error", "message": "Empty message"}, status=400)

            # 1️⃣ Fetch or create user profile
            profile, _ = TravelerProfile.objects.get_or_create(phone_number=sender)
            lowered = message.lower()

            # 2️⃣ Detect interests via simple keywords
            INTEREST_TAGS = {
                "food": "foodie",
                "museum": "culture",
                "spa": "wellness",
                "hike": "adventure",
                "partner": "romantic"
            }
            user_tags = {tag for keyword, tag in INTEREST_TAGS.items() if keyword in lowered}

            # 3️⃣ Parse name if introduced
            name_match = re.search(r"my name is (\w+)", lowered)
            if name_match:
                profile.name = name_match.group(1).capitalize()

            #4️⃣ Extract itinerary data: destination, dates, and plans
            itinerary_info = extract_itinerary_info(message)

            if itinerary_info and itinerary_info.get("destination"):
                profile.last_destination = itinerary_info["destination"]
            profile.save()

            # 5️⃣ Persist itinerary if all required fields exist
            if itinerary_info and all([
                itinerary_info.get("destination"),
                itinerary_info.get("start_date"),
                itinerary_info.get("end_date")
            ]):
                itinerary, created = Itinerary.objects.get_or_create(
                    user=profile,
                    destination=itinerary_info["destination"],
                    start_date=itinerary_info["start_date"],
                    end_date=itinerary_info["end_date"]
                )
                if itinerary_info.get("daily_plan"):
                    itinerary.daily_plan.update(itinerary_info["daily_plan"])
                    itinerary.save()


                # 6️⃣ Optional Day 2 nudging
                if created:
                    if "Day 1" not in itinerary_info["daily_plan"]:
                        follow_up = "✈️ Your trip is saved! Want help adding a Day 1 activity?"
                    else:
                        follow_up = f"📅 Day 1 is set for {itinerary_info['daily_plan'].get('Day 1')}. Want me to help plan Day 2?"
                    send_whatsapp_message(sender, follow_up)

            # 7️⃣ Generate GPT prompt from user context
            prompt = generate_personalized_prompt(profile, message, interest_tags=user_tags)

            # 8️⃣ Get AI-generated reply
            ai_response = llm.invoke([HumanMessage(content=prompt)]).content.strip()[:1000]
            if not ai_response:
                ai_response = "Sorry, I couldn't generate a response at the moment."

            # 9️⃣ Log conversation history
            ChatHistory.objects.create(user_id=sender, message=message)
            ChatHistory.objects.create(user_id=sender, message=ai_response)

            # 🔟 Send the reply to WhatsApp
            send_whatsapp_message(sender, ai_response)

            return JsonResponse({"status": "success", "response": ai_response})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "invalid request"}, status=400)


def send_whatsapp_message(to, message):
    if to.startswith("whatsapp:"):
        to = to.replace("whatsapp:", "")

    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
    STATUS_CALLBACK = os.getenv("TWILIO_STATUS_CALLBACK_URL")

    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
        print("[❗] Missing Twilio credentials.")
        return 500, "Twilio not configured."

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    payload = {
        "From": f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
        "To": f"whatsapp:{to}",
        "Body": message
    }
    if STATUS_CALLBACK:
        payload["StatusCallback"] = STATUS_CALLBACK

    response = requests.post(url, data=payload, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
    if response.status_code != 201:
        print(f"[🚫] Twilio error: {response.status_code}, {response.text}")
    else:
        print(f"[✅] WhatsApp message sent to {to}")

    return response.status_code, response.text


def generate_personalized_prompt(profile, user_message, interest_tags=None):
    context = []

    if profile.name:
        context.append(f"Name: {profile.name}")
    if profile.last_destination:
        context.append(f"Planned destination: {profile.last_destination}")
    if profile.travel_style:
        context.append(f"Travel style: {profile.travel_style}")
    if profile.travel_buddy:
        context.append(f"Travel companion: {profile.travel_buddy}")
    if profile.preferences:
        context.append(f"Preferences: {profile.preferences}")
    if interest_tags:
        context.append(f"Traveler type: {', '.join(interest_tags)}")

    dt = dateparser.parse(user_message)
    if dt:
        weekday = dt.strftime("%A")
        context.append(f"User is asking about plans for a {weekday}")

    # Inject today’s trip context if within an active itinerary
    today = date.today()
    active_itinerary = Itinerary.objects.filter(
        user=profile,
        start_date__lte=today,
        end_date__gte=today
    ).first()

    if active_itinerary:
        day_number = (today - active_itinerary.start_date).days + 1
        day_key = f"Day {day_number}"
        today_plan = active_itinerary.daily_plan.get(day_key)
        if today_plan:
            context.append(f"Today is {day_key} of the trip to {active_itinerary.destination}. Planned activity: {today_plan}")
        else:
            context.append(f"Today is {day_key} of the trip to {active_itinerary.destination}, but no activity is scheduled.")

    system_prompt = (
        "You are a friendly and knowledgeable travel assistant. "
        "Use the context to personalize your response."
    )
    return system_prompt + "\n\n" + "\n".join(context) + f"\n\nUser: {user_message}"


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