from django.urls import path
from .views import (
    home,
    chatbot_response,
    whatsapp_webhook,
    carousel_image,
)

urlpatterns = [
    path("", home, name="home"),
    path("response/", chatbot_response),  # Chatbot basic response
    path("webhook/", whatsapp_webhook),   # WhatsApp webhook
    path("carousel-image/<str:filename>/", carousel_image, name="carousel_image"),
]



