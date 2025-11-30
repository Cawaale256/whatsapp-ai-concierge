# concierge/tests/conftest.py
# Pytest configuration file (conftest.py)
# Provides shared fixtures for TravelerProfile, Itinerary, etc.
# These fixtures automatically seed the SQLite test database during test runs,
# ensuring fast, isolated, and realistic data setup without touching the Neon/Postgres production DB.

from django.test import Client
import pytest
pytestmark = pytest.mark.django_db
from chatbot.models import TravelerProfile, Itinerary

@pytest.fixture
def traveler():
    """Seed a sample TravelerProfile for tests."""
    return TravelerProfile.objects.create(
        phone_number="+447123456789",
        name="Alice",
        last_destination="London",
        travel_style="Budget",
        travel_buddy="Solo",
        preferences="Street food, museums"
    )

@pytest.fixture
def itinerary(traveler):
    """Seed a sample Itinerary linked to the traveler."""
    return Itinerary.objects.create(
        user=traveler,
        destination="Rome",
        start_date="2025-12-01",
        end_date="2025-12-05",
        daily_plan={"Day 1": "Colosseum", "Day 2": "Vatican"},
        timezone="Europe/Rome"
    )

@pytest.fixture(params=[
    {"name": "Alice", "phone": "+447100000001", "style": "Budget", "buddy": "Solo"},
    {"name": "Bob",   "phone": "+447100000002", "style": "Luxury", "buddy": "Couple"},
    {"name": "Cara",  "phone": "+447100000003", "style": "Adventure", "buddy": "Group"},
    {"name": "Dan",   "phone": "+447100000004", "style": "Relaxed", "buddy": "Solo"},
])
def traveler_param(request):
    data = request.param
    return TravelerProfile.objects.create(
        phone_number=data["phone"],
        name=data["name"],
        last_destination="Paris",
        travel_style=data["style"],
        travel_buddy=data["buddy"],
        preferences="Food, art, culture"
    )

@pytest.fixture
def client():
    return Client()

