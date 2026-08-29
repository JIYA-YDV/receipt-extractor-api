"""One-off smoke test: prove we can talk to the local LLM."""
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Find the absolute path to the root directory's .env file
root_dir = Path(__file__).parent.parent.parent
env_path = root_dir / ".env"

print(f"Looking for .env file at: {env_path.resolve()}")

if not env_path.exists():
    print("❌ ERROR: .env file does not exist in the root directory!")
    print("Please run: Copy-Item .env.example .env")
    exit(1)

# Load variables explicitly from the path
load_dotenv(dotenv_path=env_path)

# Verify key variables are loaded
base_url = os.environ.get("LLM_BASE_URL")
api_key = os.environ.get("LLM_API_KEY")
model = os.environ.get("LLM_MODEL")

print(f"LLM_BASE_URL: {base_url}")
print(f"LLM_API_KEY: {api_key}")
print(f"LLM_MODEL: {model}")

if not base_url or not api_key or not model:
    print("❌ ERROR: Some environment variables are missing from your .env file!")
    exit(1)

print("\nConnecting to Ollama model...")
try:
    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
    )

    res = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Reply with exactly the word: ready"}],
    )

    print(f"🤖 Model Response: {res.choices[0].message.content}")
except Exception as e:
    print(f"❌ Connection Failed: {e}")