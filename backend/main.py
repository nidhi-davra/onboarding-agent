from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import re
from typing import List

# --- Environment Variables ---
load_dotenv()

# --- Initialize OpenAI Client ---
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set!")
client = OpenAI(api_key=api_key)

app = FastAPI()

# --- CORS Middleware ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Models ---
class Message(BaseModel):
    text: str
    sender: str

class ChecklistItem(BaseModel):
    topic: str
    status: str

class ChatRequest(BaseModel):
    messages: list[Message]
    checklist: List[ChecklistItem]
    agent_type: str  # "team_lead" or "hr"

class ChatResponse(BaseModel):
    reply: Message
    checklist: List[ChecklistItem]


# --- System Prompt ---
try:
    with open("../prompt.md", "r") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    SYSTEM_PROMPT = "You are a helpful assistant."
    print("Warning: prompt.md not found. Using a default system prompt.")


# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Onboarding Agent API is running!"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    # Determine which prompt to load based on the agent_type
    prompt_file = "../prompt.md" if request.agent_type == "team_lead" else "../prompt_hr.md"
    try:
        with open(prompt_file, "r") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        system_prompt = "You are a helpful assistant."
        print(f"Warning: {prompt_file} not found. Using a default system prompt.")

    messages = [{"role": msg.sender, "content": msg.text} for msg in request.messages]
    conversation = [{"role": "system", "content": system_prompt}] + messages
    
    current_checklist = request.checklist

    try:
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation
        )
        response_text = chat_completion.choices[0].message.content
        clean_text = response_text

        # --- Process Checklist Update using a Robust Regular Expression ---
        # This regex finds the marker, is case-insensitive, and handles extra spaces or newlines.
        match = re.search(r'\|\|\s*CHECKLIST_UPDATE\s*\|\|({.*})', response_text, re.IGNORECASE | re.DOTALL)
        
        if match:
            # We take only the text *before* the marker. This is the clean response for the user.
            clean_text = response_text[:match.start()].strip()
            
            # Extract the JSON part of the marker
            update_json_str = match.group(1)
            try:
                update_data = json.loads(update_json_str)
                completed_topic = update_data.get("completed_topic")
                
                if completed_topic:
                    for item in current_checklist:
                        if item.topic == completed_topic:
                            item.status = "completed"
                            break
            except json.JSONDecodeError:
                print(f"Warning: Malformed checklist JSON from AI: {update_json_str}")
                pass
        
        # Set the next topic to "in_progress"
        in_progress_set = False
        for item in current_checklist:
            if item.status == "pending" and not in_progress_set:
                item.status = "in_progress"
                in_progress_set = True

        agent_reply = Message(text=clean_text, sender="assistant")

    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        agent_reply = Message(
            text="Sorry, I'm having trouble connecting to my brain right now. Please try again in a moment.",
            sender="assistant"
        )

    return ChatResponse(reply=agent_reply, checklist=current_checklist)

# --- Main Entry Point ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 