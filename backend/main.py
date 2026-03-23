from fastapi import FastAPI
from pydantic import BaseModel
from agent import chat
from tool_registry import execute_tool
from tool_specs import tools

app = FastAPI()

class ChatRequest(BaseModel):
    conversation_id: str = "default"
    message: str

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    response = chat(req.message, tools=tools, execute_tool=execute_tool, conversation_id=req.conversation_id)
    return {"response": response}