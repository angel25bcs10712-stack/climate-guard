import os
import base64
import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="ClimateGuard")

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("MODEL_NAME", "gemma3:4b")  # Optimized for Gemma 4 Good Track
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "gemma:2b-vision") # Vision model

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

@app.get("/", response_class=HTMLResponse)
async def read_root():
    # We will serve the index.html from templates
    return templates.TemplateResponse("index.html", {"request": {}})

@app.post("/chat")
async def chat(message: str = Form(...), disaster_type: str = Form("General"), location: str = Form("Unknown")):
    # Tool definition for Gemma 4 Function Calling
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
    
    prompt = f"Context: Disaster Type - {disaster_type}, Location - {location}\nSituation: {message}\n\nProvide guidance based on the system prompt rules. You may use the 'get_local_weather' tool if the situation depends on environmental conditions."
    
    payload = {
        "model": MODEL_NAME,
        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
        "stream": False,
        "tools": tools # Enable native function calling
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Check for tool calls (Gemma 4 specific)
        if "tool_calls" in result:
            # Mock function response for offline capability
            tool_response = "Current weather: Heavy rain, wind speeds 40km/h, temperature 22°C. No lightning detected."
            # Second call to finalize the response with tool data
            final_payload = {
                "model": MODEL_NAME,
                "prompt": f"{SYSTEM_PROMPT}\n\nSituation: {message}\nTool Output: {tool_response}",
                "stream": False
            }
            final_response = requests.post(OLLAMA_URL, json=final_payload)
            return final_response.json()
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-image")
async def analyze_image(
    file: UploadFile = File(...), 
    disaster_type: str = Form("General"), 
    location: str = Form("Unknown")
):
    contents = await file.read()
    image_base64 = base64.b64encode(contents).decode("utf-8")
    
    prompt = f"Analyze this image in the context of a {disaster_type} disaster in {location}. Identify threats and provide survival guidance."
    
    payload = {
        "model": VISION_MODEL_NAME,
        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
        "images": [image_base64],
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
