from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse

def chatbot_response(request):
    return JsonResponse({"message": "Hello! How can I assist you?"})
