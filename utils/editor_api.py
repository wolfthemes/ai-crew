from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

app = FastAPI()

# Allow frontend running on localhost (same machine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:8501"]
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.post("/save_editor_content")
async def save_editor_reply(request: Request):
    data = await request.json()
    content = data.get("html", "")

    os.makedirs("data/dynamic", exist_ok=True)
    with open("data/dynamic/tinymce_content", "w", encoding="utf-8") as f:
        f.write(content)

    return {"status": "ok", "message": "Reply saved"}
