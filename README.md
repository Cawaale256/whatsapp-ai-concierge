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

## Testing

- Unit tests written with `pytest` and `pytest-django`
- Fixtures defined in `conftest.py` to seed sample TravelerProfile and Itinerary data
- SQLite used as the test database for fast, isolated runs in Codespaces
- Integration tests run against Neon/Postgres to validate production behavior

## Running Tests
This project uses pytest with Django integration to verify functionality. Tests cover webhook behavior, itinerary creation, preference parsing, and OpenAI integration.

Step‑by‑step guide
Activate your virtual environment

bash
source myenv/bin/activate
You should see (myenv) at the start of your terminal prompt.

Install dependencies

bash:
pip install -r requirements.txt
Apply migrations Django tests use a separate database. Make sure migrations are applied:

bash:
python manage.py migrate
Run the test suite Use verbose mode (-v) to see each test name, and --reuse-db to speed up repeated runs by reusing the test database:

bash:
pytest -v --reuse-db
Example output:

Code
concierge/tests/test_webhook.py::test_webhook_valid_post PASSED
concierge/tests/test_webhook.py::test_itinerary_created_from_command PASSED
...
12 passed in 51.18s
Interpreting results

PASSED → test succeeded

FAILED → something broke; pytest will show a traceback

WARNINGS → not failures, but notes about deprecations or environment setup (safe to ignore for now)

Notes
Current warnings (Spacy deprecation, Django staticfiles, test DB teardown) are non‑blocking and will be addressed in future cleanup.

Always commit your code and requirements.txt, but never commit your virtual environment (myenv/). Use .gitignore to keep your repo clean.

## Troubleshooting
Even with all dependencies installed, you may run into a few common issues when running tests or migrations. Here’s how to fix them:

1. Missing PostgreSQL driver (psycopg2-binary)
Error message:
django.core.exceptions.ImproperlyConfigured: Error loading psycopg2 or psycopg module
Fix: Add the driver to your environment:

bash
pip install psycopg2-binary
Make sure it’s also listed in requirements.txt:

Code
psycopg2-binary==2.9.9
2. Torch installation error (torch==2.6.0+cpu)
Error message:

Code
ERROR: No matching distribution found for torch==2.6.0+cpu
Fix: Replace the line in requirements.txt with:

Code
torch==2.6.0
Then reinstall:

bash
pip install -r requirements.txt
3. Database conflicts during test teardown
Error message:

Code
OperationalError: database "concierge_test" is being accessed by other users
Fix: Run tests with the --reuse-db flag to avoid recreating the test database each time:

bash
pytest -v --reuse-db
Or ensure only one pytest session is running at a time.

4. Staticfiles warning in Django
Warning message:

Code
UserWarning: No directory at: /workspaces/whatsapp-ai-concierge/staticfiles/
Fix: Create the missing directory:

bash
mkdir staticfiles
Or update STATIC_ROOT in settings.py to point to a valid path.

5. Deprecation warnings (Spacy / Click)
Warning message:

Code
DeprecationWarning: Importing 'parser.split_arg_string' is deprecated
Fix: Safe to ignore for now. These will be resolved automatically when upgrading dependencies in the future.

# Common Setup Mistakes:
Forgetting to activate the virtual environment Always run source myenv/bin/activate before installing or testing.

Not installing dependencies Run pip install -r requirements.txt after cloning the repo.

Missing PostgreSQL driver Install psycopg2-binary if you see Error loading psycopg2 or psycopg module.

Torch install error (+cpu tag) Use torch==2.6.0 instead of torch==2.6.0+cpu.

No .env file Add Twilio and OpenAI credentials in .env before starting the server.

Staticfiles warning Create a staticfiles/ directory or update STATIC_ROOT in settings.py.

Database conflicts in tests Use pytest -v --reuse-db to avoid teardown errors.

## Repository Cleanup Notice

This project previously contained:
- A nested copy of itself (`whatsapp-ai-concierge/whatsapp-ai-concierge/`)
- Large binaries from the local Python environment (`myenv/`), including CUDA/Torch libraries

These files were mistakenly committed and caused the repository size to exceed 3 GB.  
They have now been **removed from Git history** using `git filter-repo` to ensure the repo is lightweight, maintainable, and CI‑safe.

### Current structure
- `concierge/` – Django project configuration and apps
- `chatbot/` – Views, models, templates, static files
- `tests/` – Isolated pytest files
- `.gitignore` – Excludes environments, caches, and static assets

### Important
- Repo history was rewritten. Please **re‑clone** the repository to avoid conflicts:
  ```bash
  git clone https://github.com/Cawaale256/whatsapp-ai-concierge.git



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

