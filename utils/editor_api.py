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
async def save_editor_content(request: Request):
    data = await request.json()
    content = data.get("html", "")
    ticket_id = data.get("ticket_id")

    os.makedirs("data/dynamic", exist_ok=True)
    with open(f"data/dynamic/draft_{ticket_id}", "w", encoding="utf-8") as f:
        f.write(content)

    return {"status": "ok", "message": "Reply saved"}
