# 🛡️ ClimateGuard — Offline Disaster Preparedness Assistant

> **Gemma 4 Good Hackathon** | Kaggle × Google DeepMind | May 2026

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![Ollama](https://img.shields.io/badge/Ollama-offline--first-orange.svg)](https://ollama.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

**ClimateGuard** is a fully offline AI assistant that provides life-saving, real-time disaster guidance to communities in climate-vulnerable regions. Powered by **Gemma 3 4B via Ollama (`gemma3:4b`)** by default, with a drop-in path for Gemma 4 variants.

---

## 🎯 Problem

Billions of people in rural Bangladesh, Sub-Saharan Africa, and Pacific Island nations face floods, wildfires, and extreme heat every year. When disaster strikes, **internet and power go down first**. Most AI tools require cloud connectivity — so the people who need help most get none.

**ClimateGuard puts life-saving AI directly on the device.**

---

## 🚀 Key Features

- **🔌 Zero Internet Required** — Powered by Gemma via Ollama, runs 100% on-device
- **📷 Multimodal Analysis** — Upload a photo of a threat (flood, smoke, landslide) for visual AI assessment
- **🌐 Multilingual** — Responds in English + Hindi translation for Immediate Actions
- **⚡ Native Function Calling** — Gemma tool calling used for weather-aware guidance
- **🏠 6 Disaster Types** — Flood, Wildfire, Hurricane, Heatwave, Landslide, Drought
- **🔒 Privacy First** — No data ever leaves the device

---

## 🔧 Tech Stack

| Component | Technology |
|---|---|
| AI Model | Gemma via Ollama (default: `gemma3:4b`) |
| Fine-tuning | Unsloth QLoRA (4-bit, Kaggle T4 GPU) |
| Backend | Python + FastAPI (async) |
| Frontend | Vanilla HTML/CSS/JS |
| Image Analysis | Gemma multimodal vision |
| Function Calling | Native Gemma 4 tool use |

---

## 🛠️ Setup Instructions

### 1. Install Ollama
Download from [ollama.com](https://ollama.com) and pull the model:
```bash
ollama pull gemma3:4b
```

### 2. Clone & Install Dependencies
```bash
git clone https://github.com/angel25bcs10712-stack/climate-guard.git
cd climate-guard
pip install -r requirements.txt
```

### 3. Run the App
Open **two terminals**:

**Terminal 1:**
```bash
ollama serve
```

**Terminal 2:**
```bash
python main.py
```

Open **http://localhost:8000** in your browser ✅

Optional environment variables:
```bash
set OLLAMA_BASE_URL=http://localhost:11434
set MODEL_NAME=gemma3:4b
set VISION_MODEL_NAME=gemma3:4b
```

---

## 📂 Project Structure

```
climate-guard/
├── main.py                 # FastAPI backend — chat, image analysis, function calling
├── templates/
│   └── index.html          # Full web UI — disaster selector, chat, photo upload
├── finetune_gemma.py       # Unsloth QLoRA fine-tuning script
├── training_data.json      # Disaster preparedness Q&A training dataset
├── requirements.txt        # Python dependencies
├── TECHNICAL_WRITEUP.md    # Full technical documentation
└── README.md
```

---

## 🏆 Prize Tracks

| Track | How We Qualify |
|---|---|
| **Global Resilience — Climate & Green Energy** | Core use case: offline climate disaster guidance |
| **Ollama Special Mention** | Entire inference runs via Ollama locally |
| **Unsloth Special Mention** | Fine-tuned Gemma on disaster data using Unsloth QLoRA |
| **Impact Category** | Serves underserved rural communities with zero connectivity |

---

## 🌍 Real-World Impact

ClimateGuard targets communities in:
- **Rural India** (floods, heatwaves) — Hindi language support included
- **Bangladesh** (cyclones, floods)
- **Sub-Saharan Africa** (drought, extreme heat)
- **Pacific Islands** (hurricanes, storm surge)

A single laptop running ClimateGuard can serve an **entire village** — no WiFi, no cloud, no subscription.

---

## 📋 Submission Checklist

- ✅ Working demo (FastAPI app)
- ✅ Public GitHub repository
- ✅ Technical writeup (`TECHNICAL_WRITEUP.md`)
- ✅ Fine-tuning script (`finetune_gemma.py`) + training data
- ✅ Lightweight evaluation script (`evaluate.py`) + Kaggle-ready report output
- ✅ Multimodal (photo input)
- ✅ Native function calling
- ✅ Ollama deployment
- ✅ Unsloth fine-tuning
- ⬜ Demo video *(recording May 14-15)*
- ⬜ Kaggle notebook *(uploading May 10)*

---

## 📊 Lightweight Evaluation

Run a reproducible local sanity-check and generate a report snippet for Kaggle:

```bash
python evaluate.py --model gemma3:4b --dataset training_data.json
```

Or use the stronger benchmark set:

```bash
python evaluate.py --base-url http://localhost:11434 --model gemma3:4b --dataset eval_samples.json
```

This writes:
- `eval_results.json` (raw metrics + per-sample results)
- `eval_report.md` (paste-ready markdown section for your writeup)

---

## 📜 License

Apache 2.0 — same as Gemma 4

---

*Built with ❤️ for communities where WiFi is a luxury but climate threats are a reality.*
*Gemma 4 Good Hackathon · Kaggle × Google DeepMind · April–May 2026*
