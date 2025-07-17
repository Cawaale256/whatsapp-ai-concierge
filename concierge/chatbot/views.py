import os
import requests
from requests.auth import HTTPBasicAuth
import traceback
from datetime import date
from dotenv import load_dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from .models import TravelerProfile, ChatHistory, Itinerary
from .utils.preferences import detect_interest_tags, scan_preferences
from .utils.prompt_builder import generate_personalized_prompt
from .utils.itinerary import extract_itinerary_info
from django.shortcuts import render


# Load environment variables from .env file
load_dotenv()

# Initialize GPT-4o via LangChain
llm = ChatOpenAI(model_name="gpt-4o")


from .models import Itinerary

def home(request):
    # For demo, fetch the first itinerary (you’ll want to filter by user later)
    itinerary = Itinerary.objects.first()
    return render(request, "home.html", {"itinerary": itinerary})

# Basic healthcheck for debugging
def chatbot_response(request):
    return JsonResponse({"message": "Hello from chatbot_response!"})


#  WhatsApp webhook listener for incoming messages
@csrf_exempt
def whatsapp_webhook(request):
    if request.method != "POST":
        return JsonResponse({"status": "invalid request"}, status=400)

    try:
        # 🔄 Extract message data
        message = request.POST.get("Body", "").strip()
        sender = request.POST.get("From", "").strip()
        if not message:
            return JsonResponse({"status": "error", "message": "Empty message"}, status=400)

        # 👤 Get or create user profile
        profile, _ = TravelerProfile.objects.get_or_create(phone_number=sender)
        lowered = message.lower()

        # 🎯 Detect interest tags using keyword mapping
        user_tags = detect_interest_tags(lowered)
        profile.preferences = ", ".join(user_tags)

        # 🧑 Extract name if user introduces themselves
        import re
        name_match = re.search(r"my name is (\w+)", lowered)
        if name_match:
            profile.name = name_match.group(1).capitalize()

        # 📅 Parse itinerary details from message
        itinerary_info = extract_itinerary_info(message)
        if itinerary_info.get("destination"):
            profile.last_destination = itinerary_info["destination"]
        profile.save()

        # 🗂️ Store itinerary if all essential fields are present
        if all([
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

            # 📝 Prompt user to add Day 2 or more details
            if created:
                follow_up = (
                    "✈️ Your trip is saved! Want help adding a Day 1 activity?"
                    if "Day 1" not in itinerary_info["daily_plan"]
                    else f"📅 Day 1 is set for {itinerary_info['daily_plan'].get('Day 1')}. Want me to help plan Day 2?"
                )
                send_whatsapp_message(sender, follow_up)

        # 💬 Generate LLM prompt based on user context
        prompt = generate_personalized_prompt(profile, message, interest_tags=user_tags)

        # 🤖 Call GPT-4o for response
        ai_response = llm.invoke([HumanMessage(content=prompt)]).content.strip()[:1000]
        if not ai_response:
            ai_response = "Sorry, I couldn't generate a response at the moment."

        # 🧾 Log the message and reply
        ChatHistory.objects.create(user_id=sender, message=message)
        ChatHistory.objects.create(user_id=sender, message=ai_response)

        # 📊 Update preference frequency based on entire message history
        pref_freq = scan_preferences(sender)
        profile.preferences = ", ".join(f"{tag}({count})" for tag, count in pref_freq.items())
        profile.save()

        # 📤 Send AI reply to WhatsApp
        send_whatsapp_message(sender, ai_response)

        # ✅ Return success response to Twilio
        response = JsonResponse({"status": "success", "response": ai_response})
        response["ngrok-skip-browser-warning"] = "true"
        return response

    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
    

def send_whatsapp_message(to, message):
    # Remove 'whatsapp:' prefix if present, but keep the '+' for phone numbers
    if to.startswith("whatsapp:"):
        to = to[len("whatsapp:"):]  

    # Load Twilio credentials from environment variables
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
    STATUS_CALLBACK = os.getenv("TWILIO_STATUS_CALLBACK_URL")  # Optional for delivery tracking

    # Verify that required credentials are present
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
        print("[❗] Missing Twilio credentials.")
        return 500, "Twilio not configured."

    # Construct the Twilio Messages API URL
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"

    # Prepare the message payload
    payload = {
        "From": f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
        "To": f"whatsapp:{to}",
        "Body": message
    }

    # Optionally include a status callback URL
    if STATUS_CALLBACK:
        payload["StatusCallback"] = STATUS_CALLBACK

    # Make the POST request to Twilio API with basic authentication
    response = requests.post(url, data=payload, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))

    # Log result to console based on response status
    if response.status_code != 201:
        print(f"[🚫] Twilio error: {response.status_code}, {response.text}")
    else:
        print(f"[✅] WhatsApp message sent to {to}")

    # Return the HTTP status and Twilio response text
    return response.status_code, response.text

    
   
