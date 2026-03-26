import os
from datetime import datetime

class FileSystem:
    async def save_upload(self, file, session_id: str):
        session_dir = f"uploads/{session_id}"
        os.makedirs(session_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
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
    
    async def list_files(self, session_id: str):
        session_dir = f"uploads/{session_id}"
        files = []
        
        if os.path.exists(session_dir):
            for f in os.listdir(session_dir):
                path = f"{session_dir}/{f}"
                files.append({
                    "name": f,
                    "size": os.path.getsize(path),
                    "download_url": f"/download/{session_id}/{f}"
                })
        
        return {"files": files}
