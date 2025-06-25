from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from .models import TravelerProfile, ChatHistory  # Import models for personalization and logging
# Load environment variables
load_dotenv()

# Initialize LangChain's GPT-4o model
llm = ChatOpenAI(model_name="gpt-4o")

def chatbot_response(request):
    return JsonResponse({"message": "Hello from chatbot_response!"})

# Initialize the GPT-4o model using LangChain wrapper
llm = ChatOpenAI(model_name="gpt-4o")

@csrf_exempt  # Disable CSRF protection for webhook POST requests from Twilio
def whatsapp_webhook(request):
    if request.method == "POST":  # Only process POST requests
        try:
            # Extract the WhatsApp message content and sender's phone number
            message = request.POST.get("Body", "")
            sender = request.POST.get("From", "")

            # If the message is empty, return an error response
            if not message.strip():
                return JsonResponse({"status": "error", "message": "Empty message"}, status=400)

            # Get or create a user profile based on the WhatsApp number
            profile, _ = TravelerProfile.objects.get_or_create(phone_number=sender)

            # Lowercase the message for simple string checks
            lowered = message.lower()

            # Extract and store the name if the message contains "my name is"
            if "my name is" in lowered:
                profile.name = message.split("my name is")[-1].strip().split()[0]

            # Store destination if "china" is mentioned (extendable with more logic)
            if "china" in lowered:
                profile.last_destination = "China"

            # Save the updated profile
            profile.save()

            # Personalize the prompt using the user's stored name
            user_name = profile.name or "traveler"
            #prompt = f"{user_name}, {message}"
            prompt = generate_personalized_prompt(profile, message)
  

            # Send prompt to GPT-4o and get AI-generated response
            ai_response = llm.invoke([HumanMessage(content=prompt)]).content

            # Trim response to fit within Twilio's 500 character limit
            ai_response = ai_response.strip()[:500]

            # Fallback response if AI returns empty content
            if not ai_response:
                ai_response = "Sorry, I'm unable to generate a response at the moment."

            # Log both user message and AI response in chat history
            ChatHistory.objects.create(user_id=sender, message=message)
            ChatHistory.objects.create(user_id=sender, message=ai_response)

            # Send the AI-generated message back to the user on WhatsApp
            send_whatsapp_message(sender, ai_response)

            # Return a success response to Twilio
            return JsonResponse({"status": "success", "response": ai_response})

        except Exception as e:
            # Catch unexpected errors and return a JSON-formatted error message
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    # Handle unsupported request methods (e.g., GET)
    return JsonResponse({"status": "invalid request"}, status=400)


def send_whatsapp_message(to, message):
    if to.startswith("whatsapp:"):
        to = to.replace("whatsapp:", "")

    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
        print("[❗] Missing Twilio environment variables.")
        return 500, "Twilio credentials not set."

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"

    STATUS_CALLBACK = os.getenv("TWILIO_STATUS_CALLBACK_URL")
    payload = {
        "From": f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
        "To": f"whatsapp:{to}",
        "Body": message
    }

    if STATUS_CALLBACK:  # Only include it if it's a real URL
        payload["StatusCallback"] = STATUS_CALLBACK
    print(f"[📤] Sending WhatsApp message to {to}")
    print(f"[📝] Message content: {repr(message)}")

    response = requests.post(url, data=payload, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))

    if response.status_code != 201:
        print(f"[🚫] Twilio Response Failed: {response.status_code}")
        print(f"[📄] Twilio Response Text: {response.text}")
    else:
        print(f"[✅] WhatsApp message successfully sent to {to}")

    return response.status_code, response.text


def generate_personalized_prompt(profile, user_message):
    context = []

    if profile.name:
        context.append(f"Name: {profile.name}")
    if profile.last_destination:
        context.append(f"Last destination: {profile.last_destination}")
    if profile.travel_style:
        context.append(f"Travel style: {profile.travel_style}")
    if profile.travel_buddy:
        context.append(f"Travel companion: {profile.travel_buddy}")
    if profile.preferences:
        context.append(f"Preferences: {profile.preferences}")

    system_prompt = (
        "You are a friendly and knowledgeable travel assistant. "
        "Use the context provided to personalize your response."
    )

    full_prompt = system_prompt + "\n\n" + "\n".join(context) + f"\n\nUser: {user_message}"
    return full_prompt

