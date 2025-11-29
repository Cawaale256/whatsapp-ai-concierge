# WhatsApp AI Travel Concierge

A conversational AI platform that helps travelers plan and manage their trips via WhatsApp. Built with Django, LangChain, and GPT-4o, this concierge system delivers personalized itinerary suggestions, destination insights, and real-time support.

## User Stories

- As a traveller, I want to ask the AI concierge questions via WhatsApp so that I can receive instant responses about destinations, transportation, and accommodations.
- As a frequent traveller, I want the AI concierge to remember my preferences and past interactions so that I receive personalized recommendations for my next trip.
- As a developer building my portfolio, I want to simulate how a business owner could integrate tourism services with the AI concierge via WhatsApp so that I can showcase automated customer support capabilities.
- As a user, I want my conversation history to be securely stored so that I can revisit past interactions without losing important travel information.


## Features

- WhatsApp integration via Twilio Webhook
- GPT-4o-powered responses using LangChain
- RAG pipeline for personalized travel recommendations
- Dynamic itinerary creation and updates
- User profiling and preference detection
- PostgreSQL-based chat history and metadata storage

## Future Template Structure

> **Status:** Planned – current project uses a simplified template layout for faster development.  
> This structure will be adopted in a future update for improved maintainability, scalability, and readability.

### Proposed Directory Tree
<img width="231" height="612" alt="Screenshot 2025-08-16 160517" src="https://github.com/user-attachments/assets/4819842a-06b9-49b3-99bc-99ab7af2e3ab" />

### Rendering Flow
<img width="1024" height="1024" alt="Copilot_20250816_162816" src="https://github.com/user-attachments/assets/948f6186-3789-4cc7-82be-7f6c7732033b" />

## Tech Stack

- **Backend**: Django, Python
- **AI**: LangChain, LlamaIndex, OpenAI GPT-4o
- **Messaging**: Twilio WhatsApp API
- **Database**: PostgreSQL
- **Deployment**: Docker-ready, cloud-compatible

## Setup

1. Clone the repo  
2. Add `.env` with Twilio & OpenAI credentials  
3. Run migrations and start server  
4. Connect webhook to Twilio sandbox
5. Start ngrok: `ngrok http 8000`  
6. Set Twilio webhook to: `https://<your-ngrok-url>/chatbot/webhook/`

