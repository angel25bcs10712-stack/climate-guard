import argparse
import json
import time
from pathlib import Path
from statistics import mean
from typing import Dict, List, Tuple

import httpx

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
You work FULLY OFFLINE - never tell users to check websites or apps."""

REQUIRED_HEADERS = [
    "⚠️ Immediate Actions",
    "🏠 Shelter",
    "📦 Supplies",
    "📞 Contacts",
]


def build_prompt(instruction: str, context: str) -> str:
    return (
        f"Context: {context}\n"
        f"Situation: {instruction}\n\n"
        "Provide life-saving guidance. Use the required section format exactly."
    )


def score_response(text: str) -> Tuple[float, Dict[str, bool], bool]:
    header_hits = {h: (h in text) for h in REQUIRED_HEADERS}
    structure_score = sum(header_hits.values()) / len(REQUIRED_HEADERS)
    banned_web_language = any(
        bad_phrase in text.lower()
        for bad_phrase in ["check website", "open app", "go online", "search internet"]
    )
    return structure_score, header_hits, banned_web_language


def evaluate(
    dataset_path: Path,
    model_name: str,
    ollama_generate_url: str,
    ollama_chat_url: str,
    timeout_s: float,
) -> Dict:
    rows = json.loads(dataset_path.read_text(encoding="utf-8"))
    results: List[Dict] = []
    latencies_ms: List[float] = []

    with httpx.Client(timeout=timeout_s) as client:
        for i, row in enumerate(rows, start=1):
            instruction = row.get("instruction", "")
            context = row.get("context", "")
            prompt = build_prompt(instruction, context)

            start = time.perf_counter()
            resp = client.post(
                ollama_generate_url,
                json={
                    "model": model_name,
                    "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
                    "stream": False,
                },
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies_ms.append(elapsed_ms)
            if resp.status_code == 404:
                # Some runtimes only expose /api/chat.
                chat_resp = client.post(
                    ollama_chat_url,
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                    },
                )
                if chat_resp.status_code == 404:
                    raise RuntimeError(
                        "Neither /api/generate nor /api/chat is available. "
                        "Verify OLLAMA_BASE_URL and ensure `ollama serve` is running."
                    )
                chat_resp.raise_for_status()
                generated = chat_resp.json().get("message", {}).get("content", "")
            else:
                resp.raise_for_status()
                generated = resp.json().get("response", "")

            structure_score, header_hits, banned_web_language = score_response(generated)
            results.append(
                {
                    "id": i,
                    "context": context,
                    "structure_score": round(structure_score, 3),
                    "header_hits": header_hits,
                    "offline_violation": banned_web_language,
                    "latency_ms": round(elapsed_ms, 2),
                }
            )

    avg_structure = mean(r["structure_score"] for r in results) if results else 0.0
    offline_violations = sum(1 for r in results if r["offline_violation"])

    return {
        "dataset_size": len(results),
        "model_name": model_name,
        "avg_structure_score": round(avg_structure, 3),
        "offline_violations": offline_violations,
        "avg_latency_ms": round(mean(latencies_ms), 2) if latencies_ms else 0.0,
        "p95_latency_ms": round(sorted(latencies_ms)[int(0.95 * (len(latencies_ms) - 1))], 2)
        if latencies_ms
        else 0.0,
        "samples": results,
    }


def format_kaggle_report(summary: Dict) -> str:
    return f"""## Lightweight Evaluation Report

**Model:** `{summary["model_name"]}`  
**Dataset Size:** {summary["dataset_size"]} prompts

### Aggregate Metrics
- Structure adherence (required 4 sections): **{summary["avg_structure_score"]:.3f}**
- Offline safety violations (web/app suggestions): **{summary["offline_violations"]}**
- Average latency: **{summary["avg_latency_ms"]} ms**
- P95 latency: **{summary["p95_latency_ms"]} ms**

### Method
- Ran inference locally through Ollama `/api/generate`.
- Prompted model with the same structured emergency system prompt used in the app.
- Evaluated each response for:
  1. Presence of all mandatory response headers.
  2. Basic offline-safety compliance (no advice to use websites/apps).
  3. End-to-end response latency.

### Notes
- This is a lightweight behavioral sanity-check, not a full factuality benchmark.
- Intended for reproducible project verification in hackathon writeups.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Lightweight ClimateGuard model evaluation.")
    parser.add_argument("--dataset", default="training_data.json", help="Path to JSON evaluation dataset")
    parser.add_argument("--model", default="gemma3:4b", help="Ollama model name")
    parser.add_argument("--base-url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--ollama-url", default="http://localhost:11434/api/generate", help="Ollama generate URL")
    parser.add_argument("--ollama-chat-url", default="http://localhost:11434/api/chat", help="Ollama chat URL")
    parser.add_argument("--timeout", type=float, default=60.0, help="Request timeout in seconds")
    parser.add_argument("--output-json", default="eval_results.json", help="Where to save raw JSON results")
    parser.add_argument("--output-md", default="eval_report.md", help="Where to save Kaggle-ready markdown report")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    base_url = args.base_url.rstrip("/")
    generate_url = args.ollama_url
    chat_url = args.ollama_chat_url

    # If user passed only --base-url, derive both endpoints from it.
    if args.ollama_url == "http://localhost:11434/api/generate":
        generate_url = f"{base_url}/api/generate"
    if args.ollama_chat_url == "http://localhost:11434/api/chat":
        chat_url = f"{base_url}/api/chat"

    try:
        summary = evaluate(
            dataset_path=dataset_path,
            model_name=args.model,
            ollama_generate_url=generate_url,
            ollama_chat_url=chat_url,
            timeout_s=args.timeout,
        )
    except httpx.ConnectError as exc:
        raise RuntimeError(
            "Could not connect to Ollama. Start Ollama with `ollama serve` and ensure the model is pulled."
        ) from exc

    Path(args.output_json).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    Path(args.output_md).write_text(format_kaggle_report(summary), encoding="utf-8")
    print(f"Saved JSON results to: {args.output_json}")
    print(f"Saved markdown report to: {args.output_md}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
