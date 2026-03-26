import subprocess
import io
import os
import tempfile
from contextlib import redirect_stdout, redirect_stderr

class ToolExecutor:
    async def execute_code(self, code: str, language: str = "python"):
        try:
            if language == "python":
                stdout = io.StringIO()
                stderr = io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exec(code, {"__name__": "__main__"})
                return {"success": True, "stdout": stdout.getvalue(), "stderr": stderr.getvalue()}
            
            elif language in ["bash", "sh"]:
                result = subprocess.run(code, shell=True, capture_output=True, text=True, timeout=30)
                return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
            
            elif language in ["node", "javascript"]:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                    f.write(code)
                    tmp = f.name
                result = subprocess.run(["node", tmp], capture_output=True, text=True, timeout=30)
                os.unlink(tmp)
                return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
            
            return {"success": False, "error": f"Language {language} not supported"}
        
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Execution timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def write_file(self, path: str, content: str):
        try:
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def read_file(self, path: str):
        try:
            with open(path, "r") as f:
                return {"success": True, "content": f.read()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def run_command(self, command: str):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
