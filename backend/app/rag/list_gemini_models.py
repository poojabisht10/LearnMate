import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

client = genai.Client(api_key=API_KEY)

print("\nListing available Gemini models for your API key:\n")
for model in client.models.list():
    print(f"- {model.name}")