import logging

def send_whatsapp_message(phone_number: str, message: str) -> None:
    logging.info(f"Mock send to {phone_number}: {message}")
