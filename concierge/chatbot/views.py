from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests

@csrf_exempt
def whatsapp_webhook(request):
    if request.method == "POST":
        data = json.loads(request.body)
        message = data.get("Body", "")  # Get the received message
        sender = data.get("From", "")   # Get sender's phone number

        # Example logic: Respond dynamically
        if "hello" in message.lower():
            response_message = "Hi there! How can I assist you?"
        else:
            response_message = f"You said: {message}"

        # Send response via Twilio (Replace with your credentials)
        send_whatsapp_message(sender, response_message)

        return JsonResponse({"status": "success", "response": response_message})

    return JsonResponse({"status": "invalid request"}, status=400)

def send_whatsapp_message(to, message):
    TWILIO_ACCOUNT_SID = "your_account_sid"
    TWILIO_AUTH_TOKEN = "your_auth_token"
    TWILIO_WHATSAPP_NUMBER = "whatsapp:+your_twilio_number"

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"

    payload = {
        "From": TWILIO_WHATSAPP_NUMBER,
        "To": to,
        "Body": message
    }

    headers = {
        "Authorization": f"Basic {TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}"
    }

    requests.post(url, data=payload, headers=headers)
