from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Initialize LangChain's GPT-4o model
llm = ChatOpenAI(model_name="gpt-4o")

def chatbot_response(request):
    return JsonResponse({"message": "Hello from chatbot_response!"})


@csrf_exempt
def whatsapp_webhook(request):
    if request.method == "POST":
        try:
            message = request.POST.get("Body", "")
            sender = request.POST.get("From", "")
            print(f"[📥] Received WhatsApp Message: {message} from {sender}")

            if not message.strip():
                print("[⚠️] Empty message received.")
                return JsonResponse({"status": "error", "message": "Empty message"}, status=400)

            # Generate AI-powered response using LangChain
            ai_response = llm.invoke([HumanMessage(content=message)]).content
            ai_response = ai_response.strip()[:500]  # Twilio limit safeguard

            if not ai_response:
                ai_response = "Sorry, I'm unable to generate a response at the moment."

            print(f"[🧠] AI Response: {repr(ai_response)}")

            # Send via Twilio WhatsApp API
            send_whatsapp_message(sender, ai_response)

            return JsonResponse({"status": "success", "response": ai_response})

        except Exception as e:
            print(f"[❌] Error processing webhook: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

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
