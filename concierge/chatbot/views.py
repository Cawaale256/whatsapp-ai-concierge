import os
import re
import requests
import string
import spacy
import dateparser
from dotenv import load_dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from requests.auth import HTTPBasicAuth
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from .models import TravelerProfile, ChatHistory, Itinerary

# Load env vars for Twilio
load_dotenv()

# Load SpaCy NLP model once for entity extraction
nlp = spacy.load("en_core_web_sm")

# Initialize GPT-4o using LangChain
llm = ChatOpenAI(model_name="gpt-4o")

# Entry-point ping
def chatbot_response(request):
    return JsonResponse({"message": "Hello from chatbot_response!"})

# WhatsApp Webhook
@csrf_exempt
def whatsapp_webhook(request):
    if request.method == "POST":
        try:
            message = request.POST.get("Body", "").strip()
            sender = request.POST.get("From", "").strip()

            if not message:
                return JsonResponse({"status": "error", "message": "Empty message"}, status=400)

            # 1️⃣ Get or create the user profile
            profile, _ = TravelerProfile.objects.get_or_create(phone_number=sender)

            lowered = message.lower()

            # 2️⃣ Detect traveler interests using simple keywords
            INTEREST_TAGS = {
                "food": "foodie",
                "museum": "culture",
                "spa": "wellness",
                "hike": "adventure",
                "partner": "romantic"
            }
            user_tags = {tag for keyword, tag in INTEREST_TAGS.items() if keyword in lowered}

            # 3️⃣ Extract name if provided
            name_match = re.search(r"my name is (\w+)", lowered)
            if name_match:
                profile.name = name_match.group(1).capitalize()

            # 4️⃣ Extract destination and itinerary info using NLP
            itinerary_info = extract_itinerary_info(message)

            if itinerary_info["destination"]:
                profile.last_destination = itinerary_info["destination"]

            profile.save()

            # 5️⃣ Save itinerary if valid
            if all([itinerary_info["destination"], itinerary_info["start_date"], itinerary_info["end_date"]]):
                itinerary, created = Itinerary.objects.get_or_create(
                    user=profile,
                    destination=itinerary_info["destination"],
                    start_date=itinerary_info["start_date"],
                    end_date=itinerary_info["end_date"]
                )
                
                if itinerary_info["day1_plan"]:
                    itinerary.daily_plan["Day 1"] = itinerary_info["day1_plan"]
                    itinerary.save()

                # 🪴 Prompt user to add Day 2 plan or more
                if created:
                    if not itinerary_info["day1_plan"]:
                        follow_up = "✈️ Your trip is saved! Want help adding a Day 1 activity?"
                    else:
                        follow_up = f"📅 Day 1 is set for {itinerary_info['day1_plan']}. Want me to help plan Day 2?"

                    send_whatsapp_message(sender, follow_up)    

            # 6️⃣ Compose personalized GPT prompt
            prompt = generate_personalized_prompt(profile, message, interest_tags=user_tags)

            # 7️⃣ Call GPT-4o for AI-generated reply
            ai_response = llm.invoke([HumanMessage(content=prompt)]).content.strip()[:1000]
            if not ai_response:
                ai_response = "Sorry, I couldn't generate a response at the moment."

            # 8️⃣ Save chat history
            ChatHistory.objects.create(user_id=sender, message=message)
            ChatHistory.objects.create(user_id=sender, message=ai_response)

            # 9️⃣ Send WhatsApp message back to user
            send_whatsapp_message(sender, ai_response)

            return JsonResponse({"status": "success", "response": ai_response})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "invalid request"}, status=400)


# 💬 Helper: WhatsApp Message Sender via Twilio
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

    print(f"[📤] Sending WhatsApp message to {to}")
    print(f"[📝] Message content: {repr(message)}")

    response = requests.post(url, data=payload, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))

    if response.status_code != 201:
        print(f"[🚫] Failed to send via Twilio ({response.status_code}): {response.text}")
    else:
        print(f"[✅] Message sent successfully to {to}")

    return response.status_code, response.text


# 🧠 Helper: NLP-Powered Prompt Generator
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

    # Add weekday if date is mentioned
    dt = dateparser.parse(user_message)
    if dt:
        weekday = dt.strftime("%A")
        context.append(f"User is asking about plans for a {weekday}")

    # 🧭 Inject today's itinerary if there's an active trip
    today = date.today()
    active_itinerary = Itinerary.objects.filter(
        user=profile,
        start_date__lte=today,
        end_date__gte=today
    ).first()

    if active_itinerary:
        trip_day = (today - active_itinerary.start_date).days + 1
        day_key = f"Day {trip_day}"
        today_plan = active_itinerary.daily_plan.get(day_key)

        if today_plan:
            context.append(f"Today is {day_key} of the user's trip to {active_itinerary.destination}. The planned activity: {today_plan}")
        else:
            context.append(f"Today is {day_key} of the user's trip to {active_itinerary.destination}, but no activity is scheduled yet.")

    # Compose the full prompt with system role
    system_prompt = (
        "You are a friendly and knowledgeable travel assistant. "
        "Use the context to personalize your response."
    )
    full_prompt = system_prompt + "\n\n" + "\n".join(context) + f"\n\nUser: {user_message}"

    return full_prompt    

    
# 🧳 Helper: Extract Itinerary Info Using SpaCy and DateParser
def extract_itinerary_info(user_message):
    lowered = user_message.lower()

    # Step 1: Extract up to two dates
    found_dates = search_dates(user_message)
    parsed_dates = sorted([dt.date() for _, dt in found_dates]) if found_dates else []

    start_date = parsed_dates[0] if len(parsed_dates) > 0 else None
    end_date = parsed_dates[1] if len(parsed_dates) > 1 else None

    # Step 2: Use NER to detect geographic place (city or country)
    doc = nlp(user_message)
    destination = None
    for ent in doc.ents:
        if ent.label_ == "GPE":
            destination = ent.text.title()
            break

    # Step 3: Extract Day 1 plan with regex
    day1_match = re.search(r"(first day|day one|day 1)[^\w]{0,10}([a-z\s]+)", lowered)
    day1_plan = day1_match.group(2).strip().capitalize() if day1_match else None

    print(f"[🧭] Extracted ➜ Destination: {destination}, Dates: {parsed_dates}, Day 1: {day1_plan}")

    return {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "day1_plan": day1_plan
    }
