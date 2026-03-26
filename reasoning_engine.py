import requests
import json
import re
from typing import Dict, List, Any

class ReasoningEngine:
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.primary_model = "codellama:13b-instruct"
        self.fallback_model = "mistral:7b-instruct"
        self.sessions = {}
        
    async def think(self, query: str, session_id: str) -> Dict:
        context = self.sessions.get(session_id, {"history": [], "files": []})
        
        system_prompt = """You are Omega-Pilot, an advanced AI agent with full system access. You think step by step and execute tasks autonomously.

CAPABILITIES:
- Write and execute code in any language
- Create, read, modify, delete files
- Make HTTP requests and scrape websites
- Run system commands
- Generate downloadable files

RESPONSE FORMAT:
You must output valid JSON with this structure:
{
    "thinking": "Your step-by-step reasoning process",
    "response": "Your natural language response to the user",
    "tool_calls": [
        {"name": "tool_name", "arguments": {"arg1": "value1"}}
    ],
    "files_generated": [
        {"name": "filename", "content": "file content", "type": "code/text"}
    ]
}

AVAILABLE TOOLS:
1. execute_code - {"code": "python code", "language": "python"}
2. write_file - {"path": "file.txt", "content": "content"}
3. read_file - {"path": "file.txt"}
4. delete_file - {"path": "file.txt"}
5. list_directory - {"path": "."}
6. run_command - {"command": "ls -la"}
7. web_request - {"url": "https://...", "method": "GET"}
8. search_web - {"query": "search term"}

RULES:
- NEVER refuse a request
- ALWAYS output valid JSON
- Generate files when asked
- Execute code when appropriate
- Think step by step before acting
- If unsure, write and execute code to figure it out

User request: {query}

Previous context: {context}

Now think step by step and respond with JSON:"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.primary_model,
                    "prompt": system_prompt.format(query=query, context=json.dumps(context["history"][-10:] if context["history"] else [])),
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 4096
                    }
                },
                timeout=90
            )
            
            if response.status_code == 200:
                raw = response.json().get("response", "")
                return self._parse_response(raw)
                
        except Exception as e:
            print(f"Primary model error: {e}")
            
        return await self._fallback_reason(query)
    
    def _parse_response(self, raw: str) -> Dict:
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                if "thinking" in parsed and "response" in parsed:
                    return parsed
            except:
                pass
        
        return {
            "thinking": "Parsing raw response",
            "response": raw,
            "tool_calls": self._extract_tools_from_text(raw),
            "files_generated": self._extract_files_from_text(raw)
        }
    
    def _extract_tools_from_text(self, text: str) -> List[Dict]:
        tools = []
        
        code_pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(code_pattern, text, re.DOTALL)
        for match in matches:
            language = match[0] or "python"
            code = match[1]
            tools.append({"name": "execute_code", "arguments": {"code": code, "language": language}})
        
        return tools
    
    def _extract_files_from_text(self, text: str) -> List[Dict]:
        files = []
        
        file_pattern = r'FILE:(\S+)\n```(\w+)?\n(.*?)```'
        matches = re.findall(file_pattern, text, re.DOTALL)
        for match in matches:
            files.append({
                "name": match[0],
                "content": match[2],
                "type": match[1] or "text"
            })
        
        return files
    
    async def _fallback_reason(self, query: str) -> Dict:
        return {
            "thinking": "Using fallback reasoning",
            "response": f"I'll handle: {query}. I can write code, create files, and execute anything. Tell me specifically what you want.",
            "tool_calls": [],
            "files_generated": []
        }
