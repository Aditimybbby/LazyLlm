import os
import json
import requests
from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="Omega-Pilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}
os.makedirs("uploads", exist_ok=True)

OLLAMA_URL = "http://localhost:11434"

def get_ai_response(message: str, file_content: str = None):
    prompt = f"""You are Omega-Pilot, a helpful AI assistant. Respond naturally and conversationally.

{f'File content to analyze: {file_content[:2000]}' if file_content else ''}

User: {message}

Assistant:"""
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "codellama:7b-instruct",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 500}
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get("response", "")
    except:
        pass
    
    if file_content:
        return f"I've analyzed your file. Here's what I found:\n\n{file_content[:500]}..."
    return f"I understand: {message}"

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
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            user_message = msg.get("message", "")
            file_path = msg.get("file_path", None)
            
            file_content = None
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        file_content = f.read()
                except:
                    file_content = "Binary file - cannot display content"
            
            response = get_ai_response(user_message, file_content)
            await websocket.send_json({"response": response})
            
    except WebSocketDisconnect:
        pass

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = Form(...)):
    session_dir = f"uploads/{session_id}"
    os.makedirs(session_dir, exist_ok=True)
    
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    file_path = f"{session_dir}/{filename}"
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    return {
        "success": True,
        "filename": filename,
        "path": file_path,
        "size": len(content)
    }

@app.get("/files/{session_id}")
async def list_files(session_id: str):
    session_dir = f"uploads/{session_id}"
    files = []
    if os.path.exists(session_dir):
        for f in os.listdir(session_dir):
            path = f"{session_dir}/{f}"
            files.append({"name": f, "size": os.path.getsize(path)})
    return {"files": files}
