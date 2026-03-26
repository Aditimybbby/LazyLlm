import os
import json
from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
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
    sessions[session_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                user_msg = msg.get("message", data)
            except:
                user_msg = data
            
            response = {"response": f"Received: {user_msg}. I can execute code, create files, and more."}
            
            if "code" in user_msg.lower() or "python" in user_msg.lower():
                result = await executor.execute_code("print('Hello from Omega-Pilot')", "python")
                response["execution"] = result
            
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        del sessions[session_id]

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = Form(...)):
    result = await fs.save_upload(file, session_id)
    return result

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
    result = await executor.execute_code(code, language)
    return result
