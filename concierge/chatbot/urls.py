from django.urls import path
from .views import home, chatbot_response, whatsapp_webhook  # ✅ Now includes home

urlpatterns = [
    path("", home, name="home"),
    path("response/", chatbot_response),  # Chatbot basic response
    path("webhook/", whatsapp_webhook),   # WhatsApp webhook
]
