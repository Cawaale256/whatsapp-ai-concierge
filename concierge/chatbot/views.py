from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import os
from requests.auth import HTTPBasicAuth

def chatbot_response(request):
    return JsonResponse({"message": "Hello from chatbot_response!"})

@csrf_exempt
def whatsapp_webhook(request):
    if request.method == "POST":
        try:
            # Parse incoming JSON data
            data = json.loads(request.body)
            print(f"Received WhatsApp Data: {data}")  # Log incoming data

            message = data.get("Body", "")  # Extract the message text
            sender = data.get("From", "")   # Extract sender's phone number

            # Simple chatbot response logic
            if "hello" in message.lower():
                response_message = "Hi there! How can I assist you?"
            else:
                response_message = f"You said: {message}"

            # Send response via Twilio
            send_whatsapp_message(sender, response_message)

            return JsonResponse({"status": "success", "response": response_message})

        except json.JSONDecodeError:
            print("Error decoding JSON")
            return JsonResponse({"status": "error", "message": "Invalid JSON format"}, status=400)

    return JsonResponse({"status": "invalid request"}, status=400)

def send_whatsapp_message(to, message):
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"

    payload = {
        "From": TWILIO_WHATSAPP_NUMBER,
        "To": to,
        "Body": message
    }

    # Authenticate using Twilio’s recommended method
    response = requests.post(url, data=payload, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))

    # Log Twilio's response for debugging
    print("Twilio Response:", response.status_code, response.text)

    return response.status_code, response.text
