from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from agent import process_message

app = FastAPI(title="STU Chatbot API")

# Enable CORS for the widget to connect from any website
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    sender: str
    text: str

class ChatRequest(BaseModel):
    message: str
    language: str
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    text: str
    translation: Optional[str] = ""

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # history needs to be passed as a list of dicts to the agent
        history_dicts = [{"sender": msg.sender, "text": msg.text} for msg in request.history]
        
        response_data = await process_message(
            message=request.message,
            history=history_dicts,
            language=request.language
        )
        
        return ChatResponse(
            text=response_data.get("text", ""),
            translation=response_data.get("translation", "")
        )  
        
    except Exception as e:
        import traceback
        print(f"Server error: {type(e).__name__}: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # Remove reload=True for production safety, and bind to 0.0.0.0
    uvicorn.run("main:app", host="0.0.0.0", port=port)

