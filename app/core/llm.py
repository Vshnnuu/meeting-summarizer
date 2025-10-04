import os
import re
import requests
import json
from typing import Dict, Any

def call_llm_json(prompt: str) -> Dict[str, Any]:
    provider = os.getenv("LLM_PROVIDER", "mock").lower()

    if provider == "cerebras":
        api_key = os.getenv("CEREBRAS_API_KEY")
        base_url = os.getenv("CEREBRAS_API_BASE", "https://api.cerebras.ai/v1")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # ✅ Use the correct endpoint and chat format
        url = f"{base_url}/chat/completions"
        payload = {
            "model": "llama3.1-8b",
            "messages": [
                {
                    "role": "system",
                    "content": """You are a meeting summarizer.
Return ONLY valid JSON with this structure:
{
  "summary": "string",
  "decisions": ["decision 1", "decision 2"],
  "action_items": [{"assignee": "string", "task": "string", "due_date": "string"}],
  "important_dates": ["list of dates"],
  "other_notes": ["list of notes"]
}
Do not include any explanations, comments, or text outside the JSON."""
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 800
        }

        # 🔹 Send the request
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code != 200:
            print("⚠️ Cerebras API Error:", resp.text)
            return {"summary": f"API Error: {resp.text}", "decisions": [], "action_items": [], "important_dates": [], "other_notes": []}

        data = resp.json()
        print("🟢 RAW Cerebras Response:", json.dumps(data, indent=2))

        # ✅ Extract message content safely
        content = ""
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:
            content = data.get("choices", [{}])[0].get("text", "")

        # ✅ Try JSON parsing
        try:
            return json.loads(content)
        except Exception:
            print("⚠️ Could not parse as JSON, attempting to recover...")
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass

            # fallback
            return {
                "summary": content.strip() or "⚠️ Model returned no summary.",
                "decisions": [],
                "action_items": [],
                "important_dates": [],
                "other_notes": []
            }

    # fallback (if no LLM provider)
    return {
        "summary": "...",
        "decisions": [],
        "action_items": [],
        "important_dates": [],
        "other_notes": []
    }
