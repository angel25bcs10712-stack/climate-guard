import os
import base64
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="ClimateGuard")

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
# Updated to Gemma 3 (Multimodal) for Hackathon
MODEL_NAME = os.getenv("MODEL_NAME", "gemma3:4b")  
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "gemma3:4b") 

# Templates
templates = Jinja2Templates(directory="templates")

class ChatRequest(BaseModel):
    message: str
    disaster_type: Optional[str] = "General"
    location: Optional[str] = "Unknown"

SYSTEM_PROMPT = """You are ClimateGuard, an offline AI assistant for disaster preparedness and survival.
Your goal is to provide clear, actionable, and life-saving advice.
You MUST structure your response exactly as follows:
⚠️ Immediate Actions: [List 3-5 critical steps]
🏠 Shelter: [Where to go or how to fortify current location]
📦 Supplies: [Essential items needed right now]
📞 Contacts: [Who to reach out to or signals to use]

MULTILINGUAL SUPPORT: 
If the user's situation is in Hindi, respond in Hindi. 
If in English, respond in English but include a Hindi translation for the "Immediate Actions" section.
Keep advice concise and localized if location is provided. Use a calm, authoritative tone."""

# Demo Fallback Data
DEMO_RESPONSES = {
    "Flood": "⚠️ Immediate Actions: Move to higher ground immediately. Do not walk or drive through flood waters. (तुरंत ऊंचे स्थान पर जाएं।)\n🏠 Shelter: Stay on the roof of your building if trapped. Do not go into the attic.\n📦 Supplies: Clean water, flashlight, and dry food.\n📞 Contacts: Call local emergency services or use a whistle.",
    "Wildfire": "⚠️ Immediate Actions: Evacuate the area immediately in the opposite direction of smoke. (धुएं की विपरीत दिशा में तुरंत निकल जाएं।)\n🏠 Shelter: Find a clearing away from trees or a body of water.\n📦 Supplies: N95 mask or wet cloth. Car keys and ID.\n📞 Contacts: Alert neighbors by honking your horn.",
    "General": "⚠️ Immediate Actions: Stay calm. Assess your surroundings for immediate hazards. (शांत रहें और खतरों की जांच करें।)\n🏠 Shelter: Find a sturdy building or safe open area.\n📦 Supplies: Water and first aid kit.\n📞 Contacts: Keep a radio on for emergency broadcasts."
}

async def get_ollama_response(payload):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        # Demo Fallback Logic
        disaster_type = payload.get("disaster_type", "General")
        return {
            "response": f"[DEMO MODE - OFFLINE]\n{DEMO_RESPONSES.get(disaster_type, DEMO_RESPONSES['General'])}",
            "status": "demo"
        }

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return templates.TemplateResponse("index.html", {"request": {}})

@app.post("/chat")
async def chat(message: str = Form(...), disaster_type: str = Form("General"), location: str = Form("Unknown")):
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_local_weather",
                "description": "Get current weather conditions for the user's location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    }
                }
            }
        }
    ]
    
    prompt = f"Context: Disaster Type - {disaster_type}, Location - {location}\nSituation: {message}\n\nProvide guidance. You may use tool 'get_local_weather'."
    
    payload = {
        "model": MODEL_NAME,
        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
        "stream": False,
        "tools": tools,
        "disaster_type": disaster_type # Passed for demo fallback
    }
    
    return await get_ollama_response(payload)

@app.post("/analyze-image")
async def analyze_image(
    file: UploadFile = File(...), 
    disaster_type: str = Form("General"), 
    location: str = Form("Unknown")
):
    contents = await file.read()
    image_base64 = base64.b64encode(contents).decode("utf-8")
    
    prompt = f"Analyze this image (Disaster: {disaster_type}, Location: {location}). Identify threats and provide survival guidance."
    
    payload = {
        "model": VISION_MODEL_NAME,
        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
        "images": [image_base64],
        "stream": False,
        "disaster_type": disaster_type
    }
    
    return await get_ollama_response(payload)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
