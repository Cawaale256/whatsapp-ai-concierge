# Create your models here.
from django.db import models

class ChatHistory(models.Model):
    user_id = models.CharField(max_length=255)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_id} said: {self.message[:50]}..."



class TravelerProfile(models.Model):
    phone_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, blank=True)
    last_destination = models.CharField(max_length=100, blank=True)
    travel_style = models.CharField(max_length=100, blank=True)
    travel_buddy = models.CharField(max_length=100, blank=True)
    preferences = models.TextField(blank=True)

    def __str__(self):
        return self.phone_number
    

class Itinerary(models.Model):
    user = models.ForeignKey("TravelerProfile", on_delete=models.CASCADE)
    destination = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    daily_plan = models.JSONField(blank=True, default=dict)  # e.g., {"Day 1": "Hammam + street food", ...}
    timezone = models.CharField(max_length=50, blank=True)   # optional for time-based notifications

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name}'s trip to {self.destination} ({self.start_date} → {self.end_date})"



