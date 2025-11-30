# concierge/tests/test_webhook.py
# Webhook test suite for WhatsApp AI Travel Concierge.
# Covers valid and invalid requests, multiple message sequences, itinerary creation,
# and preference parsing. Uses fixtures from conftest.py (traveler, client, etc.)
# to seed the SQLite test database and ensure fast, isolated test runs.

from django.test import Client
import pytest
from django.urls import reverse
from chatbot.models import ChatHistory, Itinerary, TravelerProfile

pytestmark = pytest.mark.django_db

def test_webhook_valid_post(client, traveler):
    response = client.post(
        reverse("chatbot:whatsapp_webhook"),
        {"Body": "Hello bot!", "From": f"whatsapp:{traveler.phone_number}"}
    )
    assert response.status_code == 200
    assert ChatHistory.objects.filter(user_id=traveler.phone_number).exists()

def test_webhook_empty_body(client, traveler):
    response = client.post(
        reverse("chatbot:whatsapp_webhook"),
        {"Body": "", "From": f"whatsapp:{traveler.phone_number}"}
    )
    assert response.status_code == 400

def test_webhook_get_request(client):
    response = client.get(reverse("chatbot:whatsapp_webhook"))
    assert response.status_code == 400

# --- Extra edge-case tests ---

def test_multiple_messages_sequence(client, traveler):
    from_num = f"whatsapp:{traveler.phone_number}"
    client.post(reverse("chatbot:whatsapp_webhook"), {"Body": "Hi", "From": from_num})
    client.post(reverse("chatbot:whatsapp_webhook"), {"Body": "Suggest Rome", "From": from_num})
    client.post(reverse("chatbot:whatsapp_webhook"), {"Body": "Book museum", "From": from_num})

    history = ChatHistory.objects.filter(user_id=traveler.phone_number).order_by("created_at")
    assert history.count() == 3
    assert history.first().message_text == "Hi"
    assert history.last().message_text == "Book museum"

@pytest.mark.parametrize("from_field", [
    "whatsapp:+44ABC",        # non-digit chars
    "whatsapp:447123",        # too short
    "whatsapp:+12345678901234567890",  # too long
    "whatsapp:",              # missing number
    "",                       # empty
    None                      # null
])
def test_invalid_phone_rejected(client, from_field):
    response = client.post(reverse("chatbot:whatsapp_webhook"),
                           {"Body": "Hello", "From": from_field})
    assert response.status_code in (400, 422)

def test_itinerary_created_from_command(client, traveler):
    from_num = f"whatsapp:{traveler.phone_number}"
    response = client.post(reverse("chatbot:whatsapp_webhook"),
                           {"Body": "plan Rome 3 days", "From": from_num})
    assert response.status_code == 200

    itin = Itinerary.objects.filter(user=traveler, destination__iexact="Rome").first()
    assert itin is not None
    assert (itin.end_date - itin.start_date).days in (2, 3)

def test_preference_parsing_updates_profile(client, traveler):
    from_num = f"whatsapp:{traveler.phone_number}"
    response = client.post(reverse("chatbot:whatsapp_webhook"),
                           {"Body": "I love street food and modern art museums", "From": from_num})
    assert response.status_code == 200

    traveler.refresh_from_db()
    assert "street food" in traveler.preferences.lower()
    assert "museum" in traveler.preferences.lower()
