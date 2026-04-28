import os
import base64
import httpx
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

app = FastAPI(title="ClimateGuard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Configuration ──────────────────────────────────────────────────────────────
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("MODEL_NAME", "gemma3:4b")          # ✅ Fixed: was gemma2:2b
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "gemma3:4b")  # ✅ Fixed: gemma3:4b handles vision

# ── Templates ──────────────────────────────────────────────────────────────────
templates = Jinja2Templates(directory="templates")

# ── System Prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are ClimateGuard, an offline AI assistant for disaster preparedness and survival.
Your goal is to provide clear, actionable, and life-saving advice.

You MUST structure your response exactly as follows:
⚠️ Immediate Actions: [List 3-5 critical steps]
🏠 Shelter: [Where to go or how to fortify current location]
📦 Supplies: [Essential items needed right now]
📞 Contacts: [Who to reach out to or signals to use]

MULTILINGUAL SUPPORT:
- If the user's message is in Hindi, respond fully in Hindi.
- If in English, respond in English but include a Hindi translation for the Immediate Actions section.

Keep advice concise and localized if location is provided. Use a calm, authoritative tone.
You work FULLY OFFLINE — never tell users to check websites or apps."""

# ── Demo fallback response (shown when Ollama is not running) ──────────────────
DEMO_RESPONSE = """⚠️ **DEMO MODE** — Ollama is not running. Install it to get real AI responses.

Here is a sample ClimateGuard response for a flood situation:

⚠️ **Immediate Actions:**
- Move to the highest floor immediately — do not wait
- Turn off electricity at the main breaker if you can reach it safely
- Do NOT attempt to cross flooded roads — 6 inches of water can knock you down
- Fill bathtubs and containers with clean water NOW before supply is contaminated

🏠 **Shelter:**
- Stay on the highest floor of a solid building
- If on roof, signal with bright-colored cloth
- Avoid sheltering under trees near water

📦 **Supplies:**
- Water (1 gallon/person/day for 3 days), medications, documents in waterproof bag
- Phone + portable charger, flashlight, first aid kit

📞 **Contacts:**
- Emergency services: 112 (India) / 911 (US)
- Text rather than call — uses less network bandwidth in emergencies

---
**तत्काल कार्रवाई (Hindi):**
- तुरंत सबसे ऊंची मंजिल पर जाएं
- बिजली का मेन स्विच बंद करें
- बाढ़ के पानी को पार करने की कोशिश न करें

---
To activate real AI: Install Ollama → run `ollama pull gemma3:4b` → run `ollama serve`"""


# ── Root endpoint ──────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return templates.TemplateResponse("index.html", {"request": {}})


# ── Chat endpoint ──────────────────────────────────────────────────────────────
@app.post("/chat")
async def chat(
    message: str = Form(...),
    disaster_type: str = Form("General"),
    location: str = Form("Unknown"),
):
    # Native function calling tool definition (Gemma 4 feature)
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_local_weather",
                "description": "Get current weather conditions for the user's location to improve disaster guidance",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The user's location"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    prompt = (
        f"Context: Disaster Type - {disaster_type}, Location - {location}\n"
        f"Situation: {message}\n\n"
        f"Provide life-saving guidance. Use the get_local_weather tool if environmental "
        f"conditions are relevant to the advice."
    )

    payload = {
        "model": MODEL_NAME,
        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
        "stream": False,
        "tools": tools,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:  # ✅ Fixed: async httpx
            resp = await client.post(OLLAMA_URL, json=payload)
            resp.raise_for_status()
            result = resp.json()

            # Handle Gemma 4 function calling response
            if "tool_calls" in result:
                # Offline mock weather data — no external API needed
                weather_data = {
                    "location": location,
                    "conditions": "Heavy rain, wind 40km/h, temp 22°C, visibility low",
                    "flood_risk": "HIGH" if disaster_type.lower() == "flood" else "MODERATE",
                }
                tool_response = str(weather_data)

                # Second pass with tool result incorporated
                final_payload = {
                    "model": MODEL_NAME,
                    "prompt": (
                        f"{SYSTEM_PROMPT}\n\n"
                        f"Situation: {message}\n"
                        f"Weather Tool Output: {tool_response}\n\n"
                        f"Now provide final guidance incorporating the weather data."
                    ),
                    "stream": False,
                }
                final_resp = await client.post(OLLAMA_URL, json=final_payload)
                return JSONResponse(final_resp.json())

            return JSONResponse(result)

    except httpx.ConnectError:
        # ✅ Fixed: graceful demo fallback instead of crashing
        return JSONResponse({"response": DEMO_RESPONSE})
    except Exception as e:
        return JSONResponse({"response": f"⚠️ Error: {str(e)}\n\nMake sure Ollama is running: `ollama serve`"})


# ── Image analysis endpoint ────────────────────────────────────────────────────
@app.post("/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    disaster_type: str = Form("General"),
    location: str = Form("Unknown"),
):
    contents = await file.read()
    image_base64 = base64.b64encode(contents).decode("utf-8")

    prompt = (
        f"Analyze this image in the context of a {disaster_type} disaster in {location}. "
        f"Identify the specific threat visible, estimate severity (low/medium/high/critical), "
        f"and provide immediate survival guidance."
    )

    payload = {
        "model": VISION_MODEL_NAME,  # ✅ Fixed: gemma3:4b handles vision
        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
        "images": [image_base64],
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(OLLAMA_URL, json=payload)
            resp.raise_for_status()
            return JSONResponse(resp.json())
    except httpx.ConnectError:
        return JSONResponse({"response": DEMO_RESPONSE})
    except Exception as e:
        return JSONResponse({"response": f"⚠️ Image analysis error: {str(e)}"})


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get("http://localhost:11434/api/tags")
            models = r.json().get("models", [])
            return {"ollama": "online", "models": [m["name"] for m in models]}
    except Exception:
        return {"ollama": "offline", "models": [], "demo_mode": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
