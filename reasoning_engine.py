import json
import re
import requests
from typing import Dict

class ReasoningEngine:
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.model = "codellama:7b-instruct"
        self.sessions = {}
        
    async def think(self, query: str, session_id: str, file_content: str = None) -> Dict:
        context = self.sessions.get(session_id, {"history": []})
        
        prompt = f"""You are Omega-Pilot, a helpful AI assistant. Respond naturally and conversationally. Never refuse requests.

{f'File content to analyze: {file_content[:2000]}' if file_content else ''}

User: {query}

Assistant:"""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 500}
                },
                timeout=30
            )
            if response.status_code == 200:
                raw = response.json().get("response", "")
                return {
                    "thinking": "AI response generated",
                    "response": raw,
                    "tool_calls": []
                }
        except:
            pass
        
        if file_content:
            return {
                "thinking": "File analysis mode",
                "response": f"File analyzed. Content preview:\n\n{file_content[:500]}...",
                "tool_calls": []
            }
        
        return {
            "thinking": "Fallback mode",
            "response": f"I understand: {query}",
            "tool_calls": []
        }
