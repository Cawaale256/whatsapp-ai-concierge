# Create your models here.
from django.db import models

class ChatHistory(models.Model):
    user_id = models.CharField(max_length=255)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class TravelerProfile(models.Model):
    phone_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, blank=True)
    last_destination = models.CharField(max_length=100, blank=True)
    travel_style = models.CharField(max_length=100, blank=True)
    travel_buddy = models.CharField(max_length=100, blank=True)
    preferences = models.TextField(blank=True)

    def __str__(self):
        return self.phone_number

