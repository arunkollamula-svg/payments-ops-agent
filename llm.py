import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "model": "openai/gpt-oss-120b",
    },
    "groq-backup": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "model": "qwen/qwen3.8-27b",
    },
}

def get_client():
    name = os.getenv("LLM_PROVIDER", "groq")
    cfg = PROVIDERS[name]
    key = os.getenv(cfg["key_env"])
    return OpenAI(base_url=cfg["base_url"], api_key=key), cfg["model"]