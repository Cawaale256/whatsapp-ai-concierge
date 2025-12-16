from django.urls import path
from . import views   # import the whole views module

app_name = "chatbot"

urlpatterns = [
    path("chat/", views.chat_page, name="chat_page"),    
    # WhatsApp webhook (Twilio will POST here)
    path("webhook/", views.whatsapp_webhook, name="whatsapp_webhook"),
    # Conversation history
    path("history/", views.chat_history, name="chat_history"),
  
]



