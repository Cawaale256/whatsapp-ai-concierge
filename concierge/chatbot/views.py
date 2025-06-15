from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import os
from requests.auth import HTTPBasicAuth
# from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI

from langchain.schema import HumanMessage
from dotenv import load_dotenv

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

            print(f"Received WhatsApp Message: {message} from {sender}")  # Debugging log

            # Generate AI-powered response using LangChain
            ai_response = llm([HumanMessage(content=message)]).content

            # Send AI response via Twilio
            send_whatsapp_message(sender, ai_response)

            return JsonResponse({"status": "success", "response": ai_response})

        except Exception as e:
            print(f"Error processing request: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "invalid request"}, status=400)

# @csrf_exempt
# def whatsapp_webhook(request):
#     if request.method == "POST":
#         try:
#             # Debug: Print full request data to verify format
#             print(f"Raw request body: {request.body.decode('utf-8')}")
#             print(f"Form data: {request.POST}")

#             # Extract message & sender (Twilio sends form-encoded data)
#             message = request.POST.get("Body", "")
#             sender = request.POST.get("From", "")

#             print(f"Received WhatsApp Message: {message} from {sender}")  # Debugging log

#             # Simple chatbot response logic
#             if "hello" in message.lower():
#                 response_message = "Hi there! How can I assist you?"
#             else:
#                 response_message = f"You said: {message}"

#             # Send response via Twilio
#             send_whatsapp_message(sender, response_message)

#             return JsonResponse({"status": "success", "response": response_message})

#         except Exception as e:
#             print(f"Error processing request: {e}")
#             return JsonResponse({"status": "error", "message": str(e)}, status=400)

#     return JsonResponse({"status": "invalid request"}, status=400)


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
