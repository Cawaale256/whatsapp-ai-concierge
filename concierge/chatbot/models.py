# Create your models here.
from django.db import models

class ChatHistory(models.Model):
    user_id = models.CharField(max_length=255)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
