import subprocess
import os
import tempfile
import requests
import json
from duckduckgo_search import DDGS
from typing import Dict, Any

class ToolExecutor:
    def __init__(self):
        self.working_dir = tempfile.mkdtemp()
        
    async def run(self, tool_name: str, arguments: Dict) -> Dict:
        if tool_name == "execute_code":
            return await self._execute_code(arguments)
        elif tool_name == "write_file":
            return await self._write_file(arguments)
        elif tool_name == "read_file":
            return await self._read_file(arguments)
        elif tool_name == "delete_file":
            return await self._delete_file(arguments)
        elif tool_name == "list_directory":
            return await self._list_directory(arguments)
        elif tool_name == "run_command":
            return await self._run_command(arguments)
        elif tool_name == "web_request":
            return await self._web_request(arguments)
        elif tool_name == "search_web":
            return await self._search_web(arguments)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    async def _execute_code(self, args: Dict) -> Dict:
        code = args.get("code", "")
        language = args.get("language", "python")
        
        try:
            if language == "python":
                import io
                from contextlib import redirect_stdout, redirect_stderr
                
                stdout = io.StringIO()
                stderr = io.StringIO()
                exec_globals = {"__name__": "__main__"}
                
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exec(code, exec_globals)
                
                return {
                    "success": True,
                    "stdout": stdout.getvalue(),
                    "stderr": stderr.getvalue()
                }
                
            elif language in ["bash", "sh"]:
                result = subprocess.run(code, shell=True, capture_output=True, text=True, timeout=60)
                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
            elif language in ["node", "javascript"]:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                    f.write(code)
                    temp = f.name
                result = subprocess.run(["node", temp], capture_output=True, text=True, timeout=60)
                os.unlink(temp)
                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _write_file(self, args: Dict) -> Dict:
        path = args.get("path", "")
        content = args.get("content", "")
        
        try:
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return {"success": True, "path": path, "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _read_file(self, args: Dict) -> Dict:
        path = args.get("path", "")
        try:
            with open(path, "r") as f:
                content = f.read()
            return {"success": True, "content": content, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _delete_file(self, args: Dict) -> Dict:
        path = args.get("path", "")
        try:
            os.remove(path)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _list_directory(self, args: Dict) -> Dict:
        path = args.get("path", ".")
        try:
            items = os.listdir(path)
            return {"success": True, "items": items, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _run_command(self, args: Dict) -> Dict:
        command = args.get("command", "")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _web_request(self, args: Dict) -> Dict:
        url = args.get("url", "")
        method = args.get("method", "GET")
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=30)
            else:
                response = requests.request(method, url, timeout=30)
            return {
                "success": True,
                "status_code": response.status_code,
                "content": response.text[:10000],
                "headers": dict(response.headers)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _search_web(self, args: Dict) -> Dict:
        query = args.get("query", "")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=10))
            return {"success": True, "results": results}
        except Exception as e:
            return {"success": False, "error": str(e)}
