from django.urls import path
from .views import (
    
    chatbot_response,
    whatsapp_webhook,
)


app_name = "chatbot"

urlpatterns = [
    path("response/", chatbot_response, name="chatbot_response"),  # Chatbot basic response
    path("webhook/", whatsapp_webhook, name="whatsapp_webhook"),   # WhatsApp webhook   
]



