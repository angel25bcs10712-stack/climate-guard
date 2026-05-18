# ClimateGuard: 100% Offline Multimodal Disaster Survival AI 🌍

## 🚨 The Problem: When the Grid Fails, You Are Blind
When severe climate disasters strike (floods, hurricanes, wildfires), the first casualties are often the power grid and cellular networks. In those critical first 72 hours, victims are left entirely cut off from the outside world.

Most existing disaster apps rely on cloud APIs, real-time databases, or high-bandwidth map services. **If you don't have internet, you don't have help.** For rural communities in South Asia, Sub-Saharan Africa, and Latin America, this lack of connectivity costs lives.

## 💡 The Solution: ClimateGuard
**ClimateGuard** is a zero-internet, zero-cloud disaster preparedness assistant that runs entirely on local hardware. By leveraging Google's **Gemma** open-weights models through local inference, ClimateGuard provides hyper-localized, multimodal survival guidance in extreme stress scenarios.

### 🌟 Key Features
* **100% Offline AI**: Runs Gemma locally via Ollama. No cloud APIs, no data costs, no internet required.
* **Global Hazard Mapping**: Offline-capable reverse geocoding via OpenStreetMap resolves your GPS coordinates to cities/states, instantly drawing localized disaster hazard radiuses (e.g., 30km Hurricane zones).
* **Multimodal Vision**: Users can take a photo of their situation (e.g., a flooded room or approaching fire). The local Gemma vision model analyzes the severity and tailors the survival plan.
* **Extreme Accessibility**: Typing is difficult during an emergency. We built **Offline Voice Input (STT)** and **Offline Read-Aloud (TTS)** natively into the browser so injured or visually impaired users can interact hands-free.
* **Automatic Bilingual Support**: If the system detects a vulnerable region (like rural India), it automatically generates guidance in both English and the local language (Hindi) side-by-side, ensuring maximum comprehension without relying on cloud translators.
* **Instant Export**: Generate a localized PDF Incident Report containing precise GPS coordinates, severity scores, and situation summaries that can be shared via Bluetooth or local mesh networks to rescue workers.

---

## 🛠️ How We Used Google Gemma
We utilized the Gemma ecosystem in two distinct ways to build a robust offline pipeline:

### 1. Fine-Tuning with Unsloth (Kaggle Environment)
We used Kaggle's T4 GPUs and the **Unsloth** library to experiment with fine-tuning the flagship dense model, **Gemma 4 31B Instruct (`unsloth/gemma-4-31b-it-bnb-4bit`)**, on our custom dataset of global survival scenarios and impact mitigation instructions.
* **Objective:** Align the model to output highly structured emergency formats (Immediate Actions, Shelter, Supplies, Contacts) and ruthlessly avoid generating conversational fluff, creating the **ClimateGuard-Gemma-4-31B** model.
* **Implementation:** We leveraged LoRA (Rank 16, Alpha 16) targeting the attention modules to adapt this 31B powerhouse for high-stress, low-latency, and hyper-reliable reasoning.

### 2. Local Inference via Ollama (Edge Environment)
For the final edge application, we wrapped the Gemma models using **Ollama** and a **FastAPI** backend to serve the frontend.
* We utilize **Gemma 3 4B (`gemma3:4b`)** as the core lightning-fast reasoning engine for standard edge devices.
* We paired it with **Gemma 3 Vision** capabilities to process user-uploaded imagery of the disaster zone.
* The system prompt was engineered to force the model to pull from its vast parametric memory of global emergency helplines (e.g., NDMA in India, NEMA in Nigeria, SES in Australia).

---

## 🏗️ Technical Architecture
* **Frontend:** Vanilla HTML/CSS/JS with Glassmorphism UI (designed for low-light/nighttime readability). Integrated with Leaflet.js for offline-capable map rendering and Web Speech APIs for STT/TTS.
* **Backend:** Python FastAPI. Handles rate-limiting, synchronous prompt engineering, and interfaces with the local LLM.
* **Model Engine:** Ollama running Gemma 3 4B (text) and Gemma 3 Vision (image).
* **Training:** Unsloth + HuggingFace TRL for QLoRA fine-tuning of Gemma 4 31B.

---

## 🌍 Impact and Future Scalability
ClimateGuard demonstrates that **cutting-edge AI doesn't need to live in a data center**. By shrinking powerful models like Gemma down to run on local laptops (and soon, mobile edge devices), we democratize survival intelligence.

In future iterations, ClimateGuard could be pre-installed on ruggedized tablets used by NGOs, embedded in local community centers, or distributed on USB drives in high-risk zones before hurricane season begins. 

When the cloud falls, ClimateGuard stays online.

---

## 🔗 Project Links
* **Live Demo URL:** [climate-guard.vercel.app](https://climate-guard-6m0aepipk-angel25bcs10712-stacks-projects.vercel.app)
* **GitHub Repository:** [angel25bcs10712-stack/climate-guard](https://github.com/angel25bcs10712-stack/climate-guard)

