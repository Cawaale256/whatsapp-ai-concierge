# concierge/tests/test_webhook.py
# Test suite for WhatsApp AI Travel Concierge webhook.
# Each test checks a specific case: valid requests, invalid requests,
# multiple messages, itinerary creation, and preference parsing.

import pytest
from django.urls import reverse
from concierge.chatbot.models import ChatHistory, TravelerProfile, Itinerary

# All tests in this file need database access
pytestmark = pytest.mark.django_db


def test_webhook_valid_post(client, traveler):
    """Webhook should accept a valid POST and return success."""
    response = client.post(
        reverse("chatbot:whatsapp_webhook"),
        {"Body": "Hello bot!", "From": f"whatsapp:{traveler.phone_number}"}
    )
    assert response.status_code == 200
    assert "WhatsApp message sent" in response.content.decode()


def test_webhook_empty_body(client, traveler):
    """Webhook should reject empty message body with 400 error."""
    response = client.post(
        reverse("chatbot:whatsapp_webhook"),
        {"Body": "", "From": f"whatsapp:{traveler.phone_number}"}
    )
    assert response.status_code == 400
    assert "Empty message" in response.content.decode()


def test_webhook_get_request(client):
    """Webhook should reject GET requests (only POST is allowed)."""
    response = client.get(reverse("chatbot:whatsapp_webhook"))
    assert response.status_code == 400
    assert "invalid request" in response.content.decode()


def test_multiple_messages_sequence(client, traveler):
    """Webhook should handle multiple messages from the same user."""
    from_num = f"whatsapp:{traveler.phone_number}"
    client.post(reverse("chatbot:whatsapp_webhook"), {"Body": "Hi", "From": from_num})
    client.post(reverse("chatbot:whatsapp_webhook"), {"Body": "Suggest Rome", "From": from_num})
    client.post(reverse("chatbot:whatsapp_webhook"), {"Body": "Book museum", "From": from_num})

    history = ChatHistory.objects.filter(user_id=traveler.phone_number)
    assert history.count() > 0  # At least one chat history record should exist


@pytest.mark.parametrize("from_field, expected_error", [
    ("whatsapp:+44ABC", "Invalid phone number"),   # invalid characters
    ("whatsapp:447123", "Invalid phone number"),   # too short
    ("whatsapp:+12345678901234567890", "Invalid phone number"),  # too long
    ("whatsapp:", "Invalid phone number"),         # missing number
    ("", "Missing sender"),                        # empty string
])
def test_invalid_phone_rejected(client, from_field, expected_error):
    """Webhook should reject invalid or missing phone numbers with 400 error."""
    response = client.post(
        reverse("chatbot:whatsapp_webhook"),
        {"Body": "Hello", "From": from_field}
    )
    assert response.status_code == 400
    assert expected_error in response.content.decode()


def test_itinerary_created_from_command(client, traveler):
    """Webhook should create an itinerary when user sends a plan command."""
    from_num = f"whatsapp:{traveler.phone_number}"
    response = client.post(
        reverse("chatbot:whatsapp_webhook"),
        {"Body": "plan Rome 3 days", "From": from_num}
    )
    assert response.status_code == 200

    # Check that itinerary was saved in the database
    itinerary = Itinerary.objects.filter(user=traveler, destination="Rome").first()
    assert itinerary is not None
    assert itinerary.destination == "Rome"


def test_preference_parsing_updates_profile(client, traveler):
    """Webhook should update traveler preferences based on message content."""
    from_num = f"whatsapp:{traveler.phone_number}"
    response = client.post(
        reverse("chatbot:whatsapp_webhook"),
        {"Body": "I love street food and modern art museums", "From": from_num}
    )
    assert response.status_code == 200

    traveler.refresh_from_db()
    # Preferences should include tags related to food and culture/museums
    prefs = traveler.preferences.lower()
    assert "foodie" in prefs or "street food" in prefs
    assert "culture" in prefs or "museum" in prefs
