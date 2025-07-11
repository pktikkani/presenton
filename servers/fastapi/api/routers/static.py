from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from pathlib import Path

static_router = APIRouter()

@static_router.get("/static/{file_path:path}")
async def serve_static_file(file_path: str):
    """Serve static files from the app directory"""
    # Construct the full file path
    base_dir = "/app"
    full_path = Path(base_dir) / file_path
    
    # Security check to prevent directory traversal
    try:
        full_path = full_path.resolve()
        if not str(full_path).startswith(base_dir):
            raise HTTPException(status_code=403, detail="Access forbidden")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path")
    
    # Check if file exists
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Return the file
    return FileResponse(
        path=str(full_path),
        filename=full_path.name,
        media_type="application/octet-stream"
    )