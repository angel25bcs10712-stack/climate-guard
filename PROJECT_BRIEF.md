# ClimateGuard - Offline Disaster Preparedness Assistant

## Project Name
ClimateGuard - Offline Disaster Preparedness Assistant

## Problem Statement
Billions of people in climate-vulnerable regions face floods, wildfires, storms, landslides, and extreme heat every year. When disasters begin, internet and power often fail first. Most AI assistants depend on cloud access, so vulnerable communities lose access exactly when guidance matters most.

ClimateGuard solves this by running life-saving AI directly on-device with zero internet dependency.

## What ClimateGuard Does
ClimateGuard is an offline-first emergency guidance assistant built for low-resource and connectivity-constrained environments.

Users can:
- Type a real situation and get immediate step-by-step survival guidance
- Upload a threat photo (floodwater, smoke, slope failure, etc.) for visual risk analysis
- Select one of six disaster categories: Flood, Wildfire, Hurricane, Heatwave, Landslide, Drought
- Provide location context for localized recommendations

All responses follow a strict emergency structure:
- Immediate Actions
- Shelter
- Supplies
- Contacts

## Tech Stack
- AI runtime: Gemma via Ollama (offline local inference)
- Fine-tuning: Unsloth QLoRA (4-bit)
- Backend: Python + FastAPI
- Frontend: Single-file HTML/CSS/JS
- Multimodal: Vision-assisted image analysis through local model inference

## Evaluation Alignment
Official page: [Gemma 4 Good Hackathon on Kaggle](https://www.kaggle.com/competitions/gemma-4-good-hackathon)

ClimateGuard maps directly to the competition's publicly described scoring dimensions:

1) Social Impact
- Targets high-risk, low-connectivity communities often excluded from AI tools
- Built for practical use under infrastructure failure

2) Technical Innovation / Execution
- Offline-first architecture with multimodal threat understanding
- Structured emergency output format for consistency in high-stress scenarios

3) Functionality / Clear Use Case
- End-to-end working app with text and image workflows
- Includes health and status endpoints for operational verification

4) Reproducibility
- Public repository with setup instructions and scripts
- Lightweight evaluation pipeline for structure, safety, and latency checks

5) Special Track Fit
- Ollama-native deployment
- Unsloth-based fine-tuning pipeline

## Target Users
- Rural and underserved communities in climate-vulnerable regions
- Field workers, local responders, NGOs, and disaster volunteers
- Schools and panchayat-level local resilience programs

## Differentiators
- Truly offline operation (not just low-bandwidth fallback)
- Multimodal threat interpretation beyond text-only interaction
- Fine-tuning-ready pipeline and evaluation artifacts
- Runs on consumer hardware with edge-friendly model options
- Strong fit for both impact and special technical prize tracks
- Demo-ready reporting UX with severity, response confidence, and incident report export/share

