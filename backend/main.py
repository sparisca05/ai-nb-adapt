import os
from typing import Optional
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import chat
from tool_registry import execute_tool
from tool_specs import tools
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", os.getenv("FRONTEND_URL")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models for request and response
class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str

class ToolCallRecord(BaseModel):
    tool: str
    args: dict
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
 
class ChatResponse(BaseModel):
    reply: str
    session_id: str
    tool_calls: list[ToolCallRecord]

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    """
    Send a message to the GitHub auditor agent.
 
    - Omit `session_id` to start a new conversation.
    - Pass the returned `session_id` in subsequent requests to maintain context.
    - `tool_calls` in the response lists every tool the agent invoked,
      in order, with arguments and final status.
    """
    session_id = req.session_id or str(uuid.uuid4())
 
    try:
        reply, tool_calls = chat(req.message, tools, execute_tool, conversation_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
    return ChatResponse(
        reply=reply,
        session_id=session_id,
        tool_calls=[ToolCallRecord(**tc) for tc in tool_calls],
    )