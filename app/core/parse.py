import json, re
from typing import Dict, Any

def coerce_json(obj) -> Dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except Exception:
            # Try to extract JSON object from text
            m = re.search(r"\{.*\}", obj, re.DOTALL)
            if m:
                return json.loads(m.group(0))
    return {"summary": "", "decisions": [], "action_items": []}
