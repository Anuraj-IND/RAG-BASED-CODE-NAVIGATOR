import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

def scaledown_compress(context: str, query: str) -> str:
    api_key = os.getenv("SCALEDOWN_API_KEY")
    if not api_key:
        return context  # safe fallback

    url = "https://api.scaledown.xyz/compress/raw/"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "context": context,
        "prompt": query,
        "scaledown": {"rate": "auto"}
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        data = res.json()
    except Exception:
        return context

    if not data.get("successful"):
        return context

    compressed = data.get("compressed_prompt")
    if not compressed:
        return context

    return compressed
