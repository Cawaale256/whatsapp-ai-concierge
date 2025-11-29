import pytest
from django.test import Client
from django.urls import reverse

@pytest.mark.django_db
def test_webhook_valid_post():
    client = Client()
    # Send a simple POST with Body and From
    response = client.post(
        reverse("chatbot:whatsapp_webhook"),
        {"Body": "Hello bot!", "From": "whatsapp:+447123456789"}
    )
    # Expect success
    assert response.status_code == 200

@pytest.mark.django_db
def test_webhook_empty_body():
    client = Client()
    # Send POST with empty Body
    response = client.post(
        reverse("chatbot:whatsapp_webhook"),
        {"Body": "", "From": "whatsapp:+447123456789"}
    )
    # Expect error
    assert response.status_code == 400

@pytest.mark.django_db
def test_webhook_get_request():
    client = Client()
    # Send GET instead of POST
    response = client.get(reverse("chatbot:whatsapp_webhook"))
    # Expect invalid request
    assert response.status_code == 400
