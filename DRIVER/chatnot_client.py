# CHATNOT Integration
import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class ChatnotClient:
    def __init__(self, api_key: str = None, base_url: str = "https://api.chatnot.com/v1"):
        self.api_key = api_key or os.getenv("CHATNOT_API_KEY")
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    def send_message(self, message: str, session_id: str = None) -> Dict[str, Any]:
        """Send a message to CHATNOT API."""
        if not self.api_key:
            return {"error": "CHATNOT_API_KEY not configured"}
        
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                headers=self.headers,
                json={"message": message, "session_id": session_id},
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def health_check(self) -> Dict[str, Any]:
        """Check CHATNOT API health."""
        if not self.api_key:
            return {"status": "unconfigured"}
        
        try:
            response = requests.get(f"{self.base_url}/health", headers=self.headers, timeout=5)
            return {"status": "connected", "data": response.json()}
        except Exception as e:
            return {"status": "error", "error": str(e)}


chatnot_client = ChatnotClient()


def chatnot_chat(message: str, session_id: str = None) -> str:
    """Send a message to CHATNOT API and return the response."""
    result = chatnot_client.send_message(message, session_id)
    
    if "error" in result:
        return f"CHATNOT error: {result['error']}"
    
    return result.get("response", str(result))


def chatnot_health() -> str:
    """Check CHATNOT API connection status."""
    result = chatnot_client.health_check()
    status = result.get("status", "unknown")
    
    if status == "connected":
        return "CHATNOT API: OK - Connected"
    elif status == "unconfigured":
        return "CHATNOT API: Not configured"
    else:
        return f"CHATNOT API: Error - {result.get('error', 'Unknown')}"