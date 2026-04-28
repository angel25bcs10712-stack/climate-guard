import os
import base64
import httpx
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict, List

app = FastAPI(title="ClimateGuard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Configuration ──────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"
MODEL_NAME = os.getenv("MODEL_NAME", "gemma3:4b")
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "gemma3:4b")

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


def _build_tools() -> List[Dict[str, Any]]:
    return [
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
                            "description": "The user's location",
                        }
                    },
                    "required": ["location"],
                },
            },
        }
    ]


def _extract_tool_calls(chat_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Ollama chat responses usually return tool calls under result.message.tool_calls.
    We also support a top-level tool_calls key for compatibility.
    """
    message = chat_result.get("message", {})
    if isinstance(message, dict) and isinstance(message.get("tool_calls"), list):
        return message["tool_calls"]
    if isinstance(chat_result.get("tool_calls"), list):
        return chat_result["tool_calls"]
    return []


def _run_mock_tool(tool_call: Dict[str, Any], disaster_type: str, location: str) -> Dict[str, Any]:
    function_payload = tool_call.get("function", {}) if isinstance(tool_call, dict) else {}
    name = function_payload.get("name", "unknown_tool")
    args = function_payload.get("arguments", {}) or {}

    selected_location = location
    if isinstance(args, dict):
        selected_location = args.get("location", location)

    if name != "get_local_weather":
        return {"error": f"Unsupported tool: {name}"}

    return {
        "location": selected_location,
        "conditions": "Heavy rain, wind 40km/h, temp 22C, visibility low",
        "flood_risk": "HIGH" if disaster_type.lower() == "flood" else "MODERATE",
    }


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
    user_prompt = (
        f"Context: Disaster Type - {disaster_type}, Location - {location}\n"
        f"Situation: {message}\n\n"
        f"Provide life-saving guidance. Use the get_local_weather tool if environmental "
        f"conditions are relevant to the advice."
    )
    tools = _build_tools()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # First pass with native tool definitions.
            resp = await client.post(
                OLLAMA_CHAT_URL,
                json={
                    "model": MODEL_NAME,
                    "messages": messages,
                    "tools": tools,
                    "stream": False,
                },
            )
            if resp.status_code < 400:
                result = resp.json()
                tool_calls = _extract_tool_calls(result)

                if tool_calls:
                    conversation = list(messages)
                    assistant_message = result.get("message", {})
                    if assistant_message:
                        conversation.append(assistant_message)

                    for tool_call in tool_calls:
                        function_payload = tool_call.get("function", {})
                        function_name = function_payload.get("name", "unknown_tool")
                        tool_output = _run_mock_tool(tool_call, disaster_type, location)
                        conversation.append(
                            {
                                "role": "tool",
                                "name": function_name,
                                "content": str(tool_output),
                            }
                        )

                    final_resp = await client.post(
                        OLLAMA_CHAT_URL,
                        json={"model": MODEL_NAME, "messages": conversation, "stream": False},
                    )
                    final_resp.raise_for_status()
                    final_json = final_resp.json()
                    final_message = final_json.get("message", {}).get("content")
                    if final_message:
                        return JSONResponse({"response": final_message})
                    return JSONResponse(final_json)

                initial_content = result.get("message", {}).get("content")
                if initial_content:
                    return JSONResponse({"response": initial_content})

            # Backward-compatible generate fallback if chat endpoint is unavailable.
            generate_resp = await client.post(
                OLLAMA_GENERATE_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": f"{SYSTEM_PROMPT}\n\n{user_prompt}",
                    "stream": False,
                },
            )
            generate_resp.raise_for_status()
            return JSONResponse(generate_resp.json())

    except httpx.ConnectError:
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
        "model": VISION_MODEL_NAME,
        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
        "images": [image_base64],
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(OLLAMA_GENERATE_URL, json=payload)
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
            r = await client.get(OLLAMA_TAGS_URL)
            models = r.json().get("models", [])
            return {"ollama": "online", "models": [m["name"] for m in models]}
    except Exception:
        return {"ollama": "offline", "models": [], "demo_mode": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
