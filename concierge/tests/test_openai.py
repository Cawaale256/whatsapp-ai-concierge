import os
from unittest.mock import MagicMock
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
run_live_test = os.getenv("RUN_OPENAI_TEST") == "1"


def run_openai_test():
    """Manual integration test with OpenAI, guarded by RUN_OPENAI_TEST flag."""
    if not api_key:
        raise ValueError("API key not found. Please set OPENAI_API_KEY in your .env file.")

    if run_live_test:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Tell me about top travel destinations."}]
        )
        print(response.choices[0].message.content)
    else:
        print("Skipping live OpenAI test. Set RUN_OPENAI_TEST=1 to run.")


def test_openai_mock():
    """Safe unit test using a mocked OpenAI client (runs in CI)."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Mocked travel destinations"))]
    )

    response = mock_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Tell me about top travel destinations."}]
    )
    assert response.choices[0].message.content == "Mocked travel destinations"


if __name__ == "__main__":
    run_openai_test()
