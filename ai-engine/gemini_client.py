
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


# Load configuration from ai-engine/.env
load_dotenv(Path(__file__).with_name(".env"))

SYSTEM_INSTRUCTION = """
You are the AI assistant for LifeOS, a personal productivity app.
Help users organize tasks, plan their day, and break goals into steps.
Be friendly, clear, and practical.
Do not claim that you created, changed, or saved tasks unless a
connected LifeOS tool confirms that action.
"""


def generate_ai_reply(message: str) -> str:
    """Generate a response using the configured Gemini model."""
    if not isinstance(message, str) or not message.strip():
        raise ValueError("message must not be empty")

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key in {
        "your_actual_api_key_here",
        "your_actual_key_here",
        "paste_your_real_key_here",
    }:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Configure it in ai-engine/.env."
        )


    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model,
        contents=message.strip(),
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "max_output_tokens": 500,
        },
    )

    reply = response.text
    if not reply or not reply.strip():
        raise RuntimeError("Gemini returned an empty response.")

    return reply.strip()
