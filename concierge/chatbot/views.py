import re
import datetime
import traceback
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import TravelerProfile, ChatHistory, Itinerary
from .utils.preferences import detect_interest_tags, scan_preferences
from .utils.prompt_builder import generate_personalized_prompt
from .utils.itinerary import extract_itinerary_info
from .utils.messaging import send_whatsapp_message 
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model_name="gpt-4o")

def valid_phone(phone: str) -> bool:
    """Validate phone numbers: must be digits with optional +, length 7–15."""
    return bool(phone and re.match(r"^\+?\d{7,15}$", phone))

@csrf_exempt
def whatsapp_webhook(request):
    if request.method != "POST":
        return JsonResponse({"status": "invalid request"}, status=400)

    try:
        message = request.POST.get("Body", "").strip()
        sender = request.POST.get("From", "").strip()

        if not message:
            return JsonResponse({"status": "error", "message": "Empty message"}, status=400)

        # Strip whatsapp: prefix
        from_number = sender.replace("whatsapp:", "")

        # Validate phone number
        if not valid_phone(from_number):
            return JsonResponse({"error": "Invalid phone number"}, status=400)

        # Get or create user profile
        profile, _ = TravelerProfile.objects.get_or_create(phone_number=from_number)
        lowered = message.lower()

        # Detect interest tags
        user_tags = detect_interest_tags(lowered)
        profile.preferences = ", ".join(user_tags)

        # Extract name
        name_match = re.search(r"my name is (\w+)", lowered)
        if name_match:
            profile.name = name_match.group(1).capitalize()

        # Parse itinerary
        itinerary_info = extract_itinerary_info(message)
        if itinerary_info.get("destination"):
            profile.last_destination = itinerary_info["destination"]
        profile.save()

        if all([itinerary_info.get("destination"),
                itinerary_info.get("start_date"),
                itinerary_info.get("end_date")]):
            itinerary, created = Itinerary.objects.get_or_create(
                user=profile,
                destination=itinerary_info["destination"],
                start_date=itinerary_info["start_date"],
                end_date=itinerary_info["end_date"]
            )
            if itinerary_info.get("daily_plan"):
                itinerary.daily_plan.update(itinerary_info["daily_plan"])
                itinerary.save()

        # Generate AI response
        prompt = generate_personalized_prompt(profile, message, interest_tags=user_tags)
        ai_response = llm.invoke([HumanMessage(content=prompt)]).content.strip()[:1000]
        if not ai_response:
            ai_response = "Sorry, I couldn't generate a response at the moment."

        # Persist chat history with timestamp
        ChatHistory.objects.create(user_id=from_number, message=message, timestamp=timezone.now())
        ChatHistory.objects.create(user_id=from_number, message=ai_response, timestamp=timezone.now())

        # Update preferences
        pref_freq = scan_preferences(from_number)
        profile.preferences = ", ".join(f"{tag}({count})" for tag, count in pref_freq.items())
        profile.save()

        # Send AI reply to WhatsApp
        send_whatsapp_message(from_number, ai_response)

        # Return response matching tests
        return JsonResponse(
            {"status": "success", "message": f"WhatsApp message sent to {from_number}"},
            status=200
        )

    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
