from fastapi import FastAPI
from pydantic import BaseModel
from src.ai_logic import chat

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    response = chat(req.message)
    return {"response": response}