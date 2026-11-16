import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GROQ_API_KEY")
if not key or not key.startswith("gsk_"):
    raise SystemExit("ERROR: .env file-il GROQ_API_KEY sheriyayi illa")

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=key)

# 1. Available models list
models = sorted(m.id for m in client.models.list().data)
print("Available models:")
for m in models:
    print("  -", m)

# 2. Test call
resp = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Reply with exactly: Groq OK"}],
)
print("\nResponse:", resp.choices[0].message.content)