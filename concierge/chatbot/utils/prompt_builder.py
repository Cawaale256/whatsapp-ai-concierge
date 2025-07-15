from datetime import date
from ..models import Itinerary
import dateparser


def generate_personalized_prompt(profile, user_message, interest_tags=None):
    context = []

    if profile.name:
        context.append(f"Name: {profile.name}")
    if profile.last_destination:
        context.append(f"Planned destination: {profile.last_destination}")
    if profile.travel_style:
        context.append(f"Travel style: {profile.travel_style}")
    if profile.travel_buddy:
        context.append(f"Travel companion: {profile.travel_buddy}")
    if profile.preferences:
        context.append(f"Preferences: {profile.preferences}")
    if interest_tags:
        context.append(f"Traveler type: {', '.join(interest_tags)}")

    dt = dateparser.parse(user_message)
    if dt:
        weekday = dt.strftime("%A")
        context.append(f"User is asking about plans for a {weekday}")

    # Inject today’s trip context if within an active itinerary
    today = date.today()
    active_itinerary = Itinerary.objects.filter(
        user=profile,
        start_date__lte=today,
        end_date__gte=today
    ).first()

    if active_itinerary:
        day_number = (today - active_itinerary.start_date).days + 1
        day_key = f"Day {day_number}"
        today_plan = active_itinerary.daily_plan.get(day_key)
        if today_plan:
            context.append(f"Today is {day_key} of the trip to {active_itinerary.destination}. Planned activity: {today_plan}")
        else:
            context.append(f"Today is {day_key} of the trip to {active_itinerary.destination}, but no activity is scheduled.")

    system_prompt = (
        "You are a friendly and knowledgeable travel assistant. "
        "Use the context to personalize your response."
    )
    return system_prompt + "\n\n" + "\n".join(context) + f"\n\nUser: {user_message}"
