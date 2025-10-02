import os, json, requests
from typing import Dict, Any

def call_llm_json(prompt: str) -> Dict[str, Any]:
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider == "cerebras":
        base = os.getenv("CEREBRAS_API_BASE", "").rstrip('/')
        key = os.getenv("CEREBRAS_API_KEY", "")
        if not base or not key:
            raise RuntimeError("Cerebras selected but CEREBRAS_API_BASE or CEREBRAS_API_KEY not set.")

        # Use chat/completions (per docs)  
        url = f"{base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama3.1-8b",  # use the model name exactly as in docs
            "messages": [
                {"role": "system", "content": "You return ONLY strict JSON. No explanations."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1024
        }

        # Debug prints
        print("🚀 Calling Cerebras:")
        print("Base:", base)
        print("URL:", url)
        print("Payload:", payload)

        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        print("🧾 Cerebras responded:", data)

        content = None
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:
            content = data.get("choices", [{}])[0].get("text", "{}")

        return json.loads(content)

    else:
        # mock
        return {
            "summary": "...",
            "decisions": [],
            "action_items": [],
            "important_dates": [],
            "other_notes": []
        }
