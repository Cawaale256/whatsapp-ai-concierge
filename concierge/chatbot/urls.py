from django.urls import path
from .views import chatbot_response, whatsapp_webhook  # Import both views

urlpatterns = [
    path("response/", chatbot_response),  # Chatbot basic response
    path("webhook/", whatsapp_webhook),   # WhatsApp webhook
]
