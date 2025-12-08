from twilio.rest import Client
import os
import logging

logger = logging.getLogger(__name__)

def send_whatsapp_message(phone_number: str, message: str) -> None:
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        client = Client(account_sid, auth_token)

        # Twilio sandbox WhatsApp number
        from_number = "whatsapp:+14155238886"

        response = client.messages.create(
            from_=from_number,
            body=message,
            to=f"whatsapp:{phone_number}"
        )
        logger.info(f"Message sent to {phone_number}, SID: {response.sid}")
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message to {phone_number}: {e}")
