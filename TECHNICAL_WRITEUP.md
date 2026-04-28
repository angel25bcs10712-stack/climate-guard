# Technical Writeup: ClimateGuard
**Project Name:** ClimateGuard — Offline Disaster Preparedness Assistant
**Hackathon:** Gemma 4 Good
**Track:** Global Resilience (Main Track) / Ollama Special Track / Unsloth Special Track

## 1. Problem Statement
ClimateGuard addresses the critical "connectivity gap" in global resilience. In climate-vulnerable regions, natural disasters frequently cripple power and internet infrastructure. By building a system that **anticipates, mitigates, and responds** to these challenges without cloud dependency, we ensure life-saving intelligence reaches those who need it most, when they need it most.

## 2. Our Solution: ClimateGuard
ClimateGuard is an offline-first assistant running on consumer hardware.
### Key Features:
- **Zero Internet Inference**: Uses Ollama to run **Gemma 3 4B (`gemma3:4b`)** locally by default.
- **Native Function Calling**: Utilizes native tool-calling to simulate local environment scans and weather data processing without a cloud connection.
- **Multilingual Support**: Supports **Hindi and English**, catering to 1B+ users in the Global South.
- **Multimodal Assessment**: Analyzes disaster photos for real-time risk evaluation.

## 3. Technical Execution
### AI Model Strategy
- **Core Runtime Model**: **Gemma 3 4B (`gemma3:4b`)** served locally via Ollama.
- **Fine-tuning Target**: **Gemma 4 4B instruct checkpoint (`unsloth/gemma-4-4b-it-bnb-4bit`)** in the training pipeline.
- **Fine-tuning**: Trained on a curated dataset of 30+ high-quality survival scenarios, optimizing for structured output in emergency contexts.
- **Function Calling**: Implemented native function definitions within the model payload to allow the AI to "think" about using local sensor tools.
- **Structured Safety Format**: Enforces a fixed emergency response layout (Immediate Actions, Shelter, Supplies, Contacts) to reduce ambiguity under stress.

### Architecture
- **Backend**: FastAPI bridge with asynchronous Ollama integration.
- **Optimization**: 4-bit quantization allows high-performance reasoning on 8GB RAM devices.
- **Frontend**: High-contrast, accessibility-first UI with 🇮🇳 Hindi localization.
- **Runtime Guardrails**: Input validation, file size/type checks for image uploads, and in-memory rate limiting for stability.
- **Observability**: Health and status endpoints expose model availability and runtime limits for rapid deployment verification.

## 4. Impact & Sustainability
ClimateGuard democratizes AI safety. By targeting the most vulnerable communities with a zero-cost, zero-data solution, we ensure that disaster preparedness is accessible to all, regardless of connectivity status.

## 5. Technical Challenges & Rationale
- **Challenge**: Enabling complex reasoning on edge devices.
- **Solution**: Native function calling in Gemma 4 allowed us to build a more interactive and tool-aware assistant without increasing model size.
- **Rationale for Multilingualism**: In the Global South, survival instructions must be in the local tongue. Adding Hindi support was critical for real-world impact.

## 6. How to Reproduce
- Repository includes `finetune_gemma.py` for Kaggle T4 GPU reproduction.
- One-command setup script provided for local Ollama deployment.
- `evaluate.py` provides lightweight reproducible checks for:
  - structured output adherence,
  - offline-safety phrasing compliance,
  - latency benchmarks.

## 7. Competitive Differentiation
- **Offline by design, not fallback**: System remains fully useful during network collapse.
- **Multimodal emergency support**: Photo-assisted hazard triage improves situational awareness.
- **Deployment realism**: Designed for resource-constrained edge environments and local operators.
- **Evaluation transparency**: Includes reproducible, local model behavior checks to support technical claims.

## 8. Judging Criteria Fit (Gemma 4 Good)
Reference: [Gemma 4 Good Hackathon on Kaggle](https://www.kaggle.com/competitions/gemma-4-good-hackathon)

- **Impact**: targets high-risk climate scenarios in low-connectivity communities.
- **Technical execution**: working multimodal FastAPI app with local model runtime, tool-calling, and runtime guardrails.
- **Clear use case**: one focused workflow - incident intake -> AI guidance -> actionable output.
- **Functionality and communication**: deterministic response format, health/status endpoints, and submission-ready docs.
- **Accessibility for constrained environments**: offline-first architecture, edge-friendly model options, and privacy-preserving local inference.
