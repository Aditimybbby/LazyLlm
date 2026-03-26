import os
import json
from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from reasoning_engine import ReasoningEngine
from tool_executor import ToolExecutor
from file_system import FileSystem

app = FastAPI(title="Omega-Pilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ReasoningEngine()
executor = ToolExecutor()
fs = FileSystem()
sessions = {}

os.makedirs("uploads", exist_ok=True)

@app.get("/")
async def index():
    with open("index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/style.css")
async def style():
    with open("style.css", "r") as f:
        return HTMLResponse(content=f.read(), media_type="text/css")

@app.get("/script.js")
async def script():
    with open("script.js", "r") as f:
        return HTMLResponse(content=f.read(), media_type="application/javascript")

@app.websocket("/ws/{session_id}")
async def websocket_handler(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    if session_id not in engine.sessions:
        engine.sessions[session_id] = {"history": []}
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                user_msg = msg.get("message", data)
            except:
                user_msg = data
            
            response = await engine.think(user_msg, session_id)
            
            if response.get("tool_calls"):
                for tool in response["tool_calls"]:
                    if tool["name"] == "execute_code":
                        result = await executor.execute_code(
                            tool["arguments"].get("code", ""),
                            tool["arguments"].get("language", "python")
                        )
                        response["execution_result"] = result
                    elif tool["name"] == "write_file":
                        result = await executor.write_file(
                            tool["arguments"].get("path", ""),
                            tool["arguments"].get("content", "")
                        )
                        response["file_result"] = result
                    elif tool["name"] == "run_command":
                        result = await executor.run_command(
                            tool["arguments"].get("command", "")
                        )
                        response["command_result"] = result
            
            await websocket.send_json(response)
            
            engine.sessions[session_id]["history"].append({
                "user": user_msg,
                "assistant": response.get("response", "")
            })
            
    except WebSocketDisconnect:
        pass

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = Form(...)):
    return await fs.save_upload(file, session_id)

@app.get("/download/{session_id}/{filename}")
async def download_file(session_id: str, filename: str):
    file_path = f"uploads/{session_id}/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    return JSONResponse({"error": "File not found"}, status_code=404)

@app.get("/files/{session_id}")
async def list_files(session_id: str):
    return await fs.list_files(session_id)

@app.post("/execute")
async def execute_code(code: str, language: str = "python"):
    return await executor.execute_code(code, language)
