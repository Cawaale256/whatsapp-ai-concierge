from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import os
from requests.auth import HTTPBasicAuth
from langchain_openai import ChatOpenAI

from langchain.schema import HumanMessage
from dotenv import load_dotenv

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

            print(f"Received WhatsApp Message: {message} from {sender}")  # Debugging log

            # Generate AI-powered response using LangChain
            # ai_response = llm([HumanMessage(content=message)]).content
            ai_response = llm.invoke([HumanMessage(content=message)]).content
            ai_response = ai_response[:1500]  # Trim to fit Twilio's limit


            # Send AI response via Twilio
            send_whatsapp_message(sender, ai_response)

            return JsonResponse({"status": "success", "response": ai_response})

        except Exception as e:
            print(f"Error processing request: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "invalid request"}, status=400)


# def send_whatsapp_message(to, message):
#     TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
#     TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
#     TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

#     url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"

#     payload = {
#     "From": f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",  # Ensure proper format
#     "To": f"whatsapp:{to}",  # Ensure recipient uses WhatsApp format
#     "Body": message
#     }


#     # Authenticate using Twilio’s recommended method
#     response = requests.post(url, data=payload, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))

#     print(f"Twilio Status Code: {response.status_code}")
#     print(f"Twilio Full Response: {response.text}")
#     return response.status_code, response.text
def send_whatsapp_message(to, message):
    # Sanitize 'to' in case it already includes 'whatsapp:'
    if to.startswith("whatsapp:"):
        to = to.replace("whatsapp:", "")

    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"

    payload = {
        "From": f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
        "To": f"whatsapp:{to}",
        "Body": message
    }

    response = requests.post(url, data=payload, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))

    print(f"Twilio Status Code: {response.status_code}")
    print(f"Twilio Full Response: {response.text}")
    return response.status_code, response.text
