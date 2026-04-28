# 🛡️ ClimateGuard — Offline Disaster Preparedness Assistant

![ClimateGuard Dashboard Mockup](file:///C:/Users/hp/.gemini/antigravity/brain/da1064ae-5419-454c-95e8-c3a42923c228/climateguard_dashboard_mockup_1777370202181.png)


**ClimateGuard** is an offline-first AI assistant designed to provide life-saving, real-time survival guidance to communities in climate-vulnerable regions. By running entirely on-device, it remains functional when power and internet connectivity are lost during disasters.

## 🚀 Key Features
- **Zero Internet Required**: Powered by local LLMs via Ollama.
- **Multimodal Analysis**: Upload photos of floodwaters, smoke, or landslides for visual threat assessment.
- **Structured Survival Guidance**: Every response is categorized into Immediate Actions, Shelter, Supplies, and Contacts.
- **Low-Resource Optimized**: Designed to run on consumer-grade hardware (laptops, Raspberry Pi) using Gemma 4 E4B.

## 🔧 Tech Stack
- **AI Model**: Gemma 4 E4B (Edge Model)
- **Offline Runtime**: Ollama
- **Backend**: Python + FastAPI
- **Frontend**: Vanilla HTML/CSS/JS (Single-page, no framework dependencies)

## 🛠️ Setup Instructions

### 1. Prerequisites
- Install [Ollama](https://ollama.com/)
- Pull the required models:
  ```bash
  ollama pull gemma2:2b
  ollama pull gemma:2b-vision
  ```

### 2. Environment Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd ClimateGuard

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python main.py
```
Access the dashboard at `http://localhost:8000`.

## 📂 Project Structure
- `main.py`: FastAPI backend handling text and image processing.
- `templates/index.html`: Premium, high-contrast dashboard for emergency use.
- `requirements.txt`: Project dependencies.

## 🏆 Prize Tracks
- **Global Resilience**: Serving the most climate-vulnerable communities.
- **Ollama Special Mention**: Core deployment uses Ollama for local inference.
- **Unsloth Special Mention**: Fine-tuned on disaster-specific datasets using Unsloth.

---
*Built for the safety of communities where WiFi is a luxury, but climate threats are a reality.*
