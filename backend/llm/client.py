"""Ollama client for local Phi-3 inference."""

import json
import os
import urllib.request

from dotenv import load_dotenv


load_dotenv()


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434",
).rstrip("/")

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "phi3:instruct",
)

REQUEST_TIMEOUT = int(
    os.getenv("OLLAMA_TIMEOUT", "120")
)

OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"


def generate_with_ollama(
    prompt: str,
    timeout: int = REQUEST_TIMEOUT,
) -> dict:
    """
    Send a prompt to the configured Ollama model.

    The function returns the decoded JSON response from Ollama.
    """

    request_data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
        },
    }

    request = urllib.request.Request(
        OLLAMA_GENERATE_URL,
        data=json.dumps(request_data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=timeout,
    ) as response:
        response_body = response.read().decode("utf-8")

    return json.loads(response_body)