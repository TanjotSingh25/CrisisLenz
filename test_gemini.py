"""
Standalone Gemini API test script.
Run this to confirm your API key works before testing the full app.

Usage (set your key first):
  docker run --rm \
    -e GEMINI_API_KEY=your_key_here \
    -v "%cd%/test_gemini.py:/test_gemini.py" \
    python:3.12-slim \
    bash -c "pip install google-genai -q && python /test_gemini.py"

Or if the backend container is running:
  docker compose exec -e GEMINI_API_KEY=your_key_here backend python /app/../test_gemini.py
"""
import os
import sys

api_key = os.environ.get("GEMINI_API_KEY", "")
model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
prompt = os.environ.get("TEST_PROMPT", "Reply with exactly: 'Gemini API is working.'")

if not api_key:
    print("ERROR: GEMINI_API_KEY environment variable is not set.")
    print("Run with: docker run --rm -e GEMINI_API_KEY=your_key ...")
    sys.exit(1)

print(f"Testing Gemini API...")
print(f"  Model : {model}")
print(f"  Prompt: {prompt}")
print()

try:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction="You are a helpful assistant.",
        ),
    )
    print("SUCCESS")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
    sys.exit(1)
