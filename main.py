import os
import base64
import time
import logging
from collections import defaultdict, deque
import httpx
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Deque, Dict, List

app = FastAPI(title="ClimateGuard")

logger = logging.getLogger("climateguard")
logging.basicConfig(level=logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if o.strip()],
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
APP_VERSION = os.getenv("APP_VERSION", "1.1.0")
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "1200"))
MAX_LOCATION_LENGTH = int(os.getenv("MAX_LOCATION_LENGTH", "120"))
MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", str(5 * 1024 * 1024)))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "40"))
_REQUEST_TRACKER: Dict[str, Deque[float]] = defaultdict(deque)

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


def _extract_response_text(payload: Dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return ""
    response = payload.get("response")
    if isinstance(response, str):
        return response
    message = payload.get("message", {})
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content
    return ""


def _normalize_user_inputs(message: str, location: str, disaster_type: str) -> Dict[str, str]:
    normalized_message = (message or "").strip()
    normalized_location = (location or "Unknown").strip()
    normalized_disaster_type = (disaster_type or "General").strip()

    if not normalized_message:
        raise ValueError("Message is required.")
    if len(normalized_message) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"Message is too long (max {MAX_MESSAGE_LENGTH} characters).")
    if len(normalized_location) > MAX_LOCATION_LENGTH:
        raise ValueError(f"Location is too long (max {MAX_LOCATION_LENGTH} characters).")

    return {
        "message": normalized_message,
        "location": normalized_location or "Unknown",
        "disaster_type": normalized_disaster_type or "General",
    }


def _rate_limit_key(request: Request) -> str:
    host = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    return f"{host}:{user_agent[:40]}"


def _enforce_rate_limit(request: Request) -> None:
    now = time.time()
    key = _rate_limit_key(request)
    bucket = _REQUEST_TRACKER[key]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
        raise RuntimeError("Rate limit exceeded. Please wait a moment and try again.")
    bucket.append(now)


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
    request: Request,
    message: str = Form(...),
    disaster_type: str = Form("General"),
    location: str = Form("Unknown"),
):
    request_start = time.perf_counter()
    try:
        _enforce_rate_limit(request)
        normalized = _normalize_user_inputs(message, location, disaster_type)
    except ValueError as e:
        return JSONResponse(status_code=422, content={"response": f"⚠️ Invalid input: {str(e)}"})
    except RuntimeError as e:
        return JSONResponse(status_code=429, content={"response": f"⚠️ {str(e)}"})

    user_prompt = (
        f"Context: Disaster Type - {normalized['disaster_type']}, Location - {normalized['location']}\n"
        f"Situation: {normalized['message']}\n\n"
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
                        tool_output = _run_mock_tool(
                            tool_call,
                            normalized["disaster_type"],
                            normalized["location"],
                        )
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
                    final_message = _extract_response_text(final_json)
                    if final_message:
                        elapsed_ms = (time.perf_counter() - request_start) * 1000
                        logger.info("chat_request_success_with_tools latency_ms=%.2f", elapsed_ms)
                        return JSONResponse({"response": final_message})
                    return JSONResponse(final_json)

                initial_content = _extract_response_text(result)
                if initial_content:
                    elapsed_ms = (time.perf_counter() - request_start) * 1000
                    logger.info("chat_request_success latency_ms=%.2f", elapsed_ms)
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
            payload = generate_resp.json()
            response_text = _extract_response_text(payload)
            elapsed_ms = (time.perf_counter() - request_start) * 1000
            logger.info("chat_request_generate_fallback latency_ms=%.2f", elapsed_ms)
            return JSONResponse({"response": response_text or str(payload)})

    except httpx.ConnectError:
        return JSONResponse({"response": DEMO_RESPONSE})
    except Exception as e:
        logger.exception("chat_request_failed")
        return JSONResponse({"response": f"⚠️ Error: {str(e)}\n\nMake sure Ollama is running: `ollama serve`"})


# ── Image analysis endpoint ────────────────────────────────────────────────────
@app.post("/analyze-image")
async def analyze_image(
    request: Request,
    file: UploadFile = File(...),
    disaster_type: str = Form("General"),
    location: str = Form("Unknown"),
):
    try:
        _enforce_rate_limit(request)
    except RuntimeError as e:
        return JSONResponse(status_code=429, content={"response": f"⚠️ {str(e)}"})

    contents = await file.read()
    if not contents:
        return JSONResponse(status_code=422, content={"response": "⚠️ Uploaded image file is empty."})
    if len(contents) > MAX_IMAGE_BYTES:
        return JSONResponse(
            status_code=413,
            content={"response": f"⚠️ Image too large. Max allowed size is {MAX_IMAGE_BYTES // (1024 * 1024)}MB."},
        )
    if not (file.content_type or "").startswith("image/"):
        return JSONResponse(status_code=415, content={"response": "⚠️ Unsupported file type. Upload an image."})

    normalized_location = (location or "Unknown").strip()[:MAX_LOCATION_LENGTH] or "Unknown"
    normalized_disaster_type = (disaster_type or "General").strip() or "General"
    image_base64 = base64.b64encode(contents).decode("utf-8")

    prompt = (
        f"Analyze this image in the context of a {normalized_disaster_type} disaster in {normalized_location}. "
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
            response_text = _extract_response_text(resp.json())
            return JSONResponse({"response": response_text or DEMO_RESPONSE})
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


@app.get("/api/status")
async def status():
    return {
        "app": "ClimateGuard",
        "version": APP_VERSION,
        "model": MODEL_NAME,
        "vision_model": VISION_MODEL_NAME,
        "limits": {
            "max_message_length": MAX_MESSAGE_LENGTH,
            "max_location_length": MAX_LOCATION_LENGTH,
            "max_image_bytes": MAX_IMAGE_BYTES,
            "rate_limit_window_seconds": RATE_LIMIT_WINDOW_SECONDS,
            "rate_limit_max_requests": RATE_LIMIT_MAX_REQUESTS,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
