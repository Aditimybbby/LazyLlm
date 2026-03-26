import os
import shutil
import aiofiles
import json
from typing import Dict, List
from datetime import datetime

class FileSystem:
    def __init__(self):
        self.base_dir = "uploads"
        
    async def save_upload(self, file, session_id: str) -> Dict:
        session_dir = os.path.join(self.base_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(session_dir, filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return {
            "success": True,
            "filename": filename,
            "path": file_path,
            "size": len(content)
        }
    
    async def save_generated_file(self, session_id: str, filename: str, content: str, file_type: str = "text") -> Dict:
        session_dir = os.path.join(self.base_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        file_path = os.path.join(session_dir, filename)
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(content)
        
        return {
            "success": True,
            "filename": filename,
            "path": file_path,
            "size": len(content),
            "download_url": f"/download/{session_id}/{filename}"
        }
    
    async def list_session_files(self, session_id: str) -> List[Dict]:
        session_dir = os.path.join(self.base_dir, session_id)
        if not os.path.exists(session_dir):
            return []
        
        files = []
        for filename in os.listdir(session_dir):
            file_path = os.path.join(session_dir, filename)
            files.append({
                "name": filename,
                "path": file_path,
                "size": os.path.getsize(file_path),
                "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                "download_url": f"/download/{session_id}/{filename}"
            })
        return files
    
    async def read_file(self, session_id: str, filename: str) -> str:
        file_path = os.path.join(self.base_dir, session_id, filename)
        async with aiofiles.open(file_path, 'r') as f:
            return await f.read()
