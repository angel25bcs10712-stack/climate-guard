# Technical Writeup: ClimateGuard
**Project Name:** ClimateGuard — Offline Disaster Preparedness Assistant
**Hackathon:** Gemma 4 Good
**Track:** Global Resilience / Ollama Special Track / Unsloth Special Track

## 1. Problem Statement
In climate-vulnerable regions like rural Bangladesh or Sub-Saharan Africa, natural disasters (floods, wildfires, extreme heat) are frequent. When these disasters strike, power and internet infrastructure are often the first to fail. Existing AI tools are almost exclusively cloud-based, rendering them useless exactly when they are needed most. ClimateGuard bridges this "digital divide" by bringing advanced AI survival intelligence entirely offline.

## 2. Our Solution: ClimateGuard
ClimateGuard is an offline-first AI assistant designed to run on consumer-grade hardware (laptops, Raspberry Pi). It provides real-time, actionable survival guidance without requiring a single byte of internet data.

### Key Features:
- **Zero Internet Inference**: Uses Ollama to run Gemma 4 locally.
- **Multimodal Threat Assessment**: Uses Gemma 4 Vision to analyze photos of disasters (e.g., rising floodwaters) and assess immediate danger.
- **Structured Guidance**: Responses are strictly formatted into Immediate Actions, Shelter, Supplies, and Contacts for maximum clarity under stress.

## 3. Technical Execution
### AI Model Strategy
- **Core Model**: Gemma 4 E4B (Edge-optimized model) fine-tuned using **Unsloth QLoRA** on a custom dataset of disaster survival manuals and climate data.
- **Vision Model**: Gemma 4 Vision for image-based threat detection.
- **Optimization**: We used 4-bit quantization to ensure the model runs smoothly on devices with as little as 8GB of RAM.

### Architecture
- **Backend**: FastAPI (Python) manages the local inference loop and multimodal processing.
- **Local Runtime**: Ollama provides the backbone for model management and local API serving.
- **Frontend**: A single-file HTML/CSS/JS dashboard designed with high-contrast aesthetics for low-visibility emergency scenarios.

## 4. Impact & Sustainability
ClimateGuard serves the most vulnerable 1 billion people who lack reliable internet but face the highest climate risk. By deploying on edge devices, we ensure that life-saving information is a human right, not a subscription service dependent on a stable connection.

## 5. Technical Challenges & Rationale
- **Challenge**: Large model sizes were too slow for emergency response on edge hardware.
- **Solution**: We chose the Gemma 4 E4B model and used Unsloth for efficient fine-tuning, reducing memory overhead while maintaining high reasoning accuracy for survival protocols.
- **Rationale for Offline-First**: Reliable connectivity is a luxury in a crisis. Local inference is the only way to guarantee 100% uptime.

## 6. How to Reproduce
- Repository includes a one-command setup via Ollama.
- Fine-tuning script provided in the Kaggle Notebook.
- Single-file frontend for portable deployment.
