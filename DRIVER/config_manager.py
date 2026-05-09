# [GOAL] Dynamic Provider Management
# [CONTEXT] Open-source project: Users plug in their own keys.

import os
from dotenv import load_dotenv

load_dotenv()

def get_provider_config():
    return {
        "primary_brain": os.getenv("PRIMARY_MODEL", "gpt-4o"),
        "openai_key": os.getenv("OPENAI_API_KEY"),
        "gemini_key": os.getenv("GOOGLE_API_KEY"),
        "anthropic_key": os.getenv("ANTHROPIC_API_KEY"),
        "tavily_key": os.getenv("TAVILY_API_KEY"),
        "chatnot_key": os.getenv("CHATNOT_API_KEY"),
    }

def get_chatnot_config():
    """Load CHATNOT credentials from credentials.json."""
    import json
    try:
        with open("credentials.json") as f:
            creds = json.load(f)
        return creds.get("chatnot", {})
    except Exception:
        return {}