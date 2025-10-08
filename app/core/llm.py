import os
import re
import requests
import json
from typing import Dict, Any

def call_llm_json(prompt: str) -> Dict[str, Any]:
    provider = os.getenv("LLM_PROVIDER", "cerebras").lower()

    if provider == "cerebras":
        api_key = os.getenv("CEREBRAS_API_KEY")
        base_url = os.getenv("CEREBRAS_API_BASE", "https://api.cerebras.ai/v1")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        url = f"{base_url}/chat/completions"
        payload = {
            "model": os.getenv("CEREBRAS_MODEL", "llama3.1-8b"),
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
            "max_tokens": 600
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            print("⚠️ Cerebras API Error:", str(e))
            return {"summary": f"API Error: {e}", "decisions": [], "action_items": [], "important_dates": [], "other_notes": []}

        print("🟢 RAW Cerebras Response:", json.dumps(data, indent=2))

        content = ""
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:
            content = data.get("choices", [{}])[0].get("text", "")

        try:
            return json.loads(content)
        except Exception:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass

            return {
                "summary": content.strip() or "⚠️ Model returned no summary.",
                "decisions": [],
                "action_items": [],
                "important_dates": [],
                "other_notes": []
            }

    return {
        "summary": "No Cerebras response.",
        "decisions": [],
        "action_items": [],
        "important_dates": [],
        "other_notes": []
    }
