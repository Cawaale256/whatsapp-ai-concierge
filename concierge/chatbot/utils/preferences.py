from ..models import ChatHistory  # Import the ChatHistory model to query user messages
# Mapping keywords to tags
INTEREST_TAGS = {
    "food": "foodie",
    "museum": "culture",
    "spa": "wellness", 
    "hike": "adventure",
    "partner": "romantic"
}

# Function to detect tags in a single message
def detect_interest_tags(lowered_msg):
    return {tag for keyword, tag in INTEREST_TAGS.items() if keyword in lowered_msg}

# Function to count tag frequency from chat history
def scan_preferences(user_id):
    frequency = {}
    for keyword, tag in INTEREST_TAGS.items():
        count = ChatHistory.objects.filter(user_id=user_id, message__icontains=keyword).count()
        if count > 0:
            frequency[tag] = count
    return frequency
