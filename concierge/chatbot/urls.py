from django.urls import path
from .views import (
    home,
    chatbot_response,
    whatsapp_webhook,
    # carousel_image,
)

app_name = "chatbot"

urlpatterns = [
    path("", home, name="home"),
    path("response/", chatbot_response, name="chatbot_response"),  # Chatbot basic response
    path("webhook/", whatsapp_webhook, name="whatsapp_webhook"),   # WhatsApp webhook
    # path("carousel-image/<str:filename>/", carousel_image, name="carousel_image"),
]



