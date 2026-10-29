from __future__ import annotations

import json
import os
import urllib.request


def gptzero(text: str, api_key: str | None = None) -> dict:
    key = api_key or os.environ.get("GPTZERO_API_KEY")
    if not key:
        return {"error": "GPTZERO_API_KEY not set"}
    url = "https://api.gptzero.me/v2/predict/text"
    data = json.dumps({"document": text}).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "x-api-key": key,
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            j = json.loads(r.read().decode())
        doc = (j.get("documents") or [{}])[0]
        return {
            "provider": "gptzero",
            "predicted_class": doc.get("predicted_class"),
            "probability_ai": doc.get("completely_generated_prob") or doc.get("overall_burstiness"),
            "raw": j,
        }
    except (OSError, ValueError, KeyError) as e:
        return {"provider": "gptzero", "error": str(e)}


def detect(text: str) -> dict:
    results = {}
    if os.environ.get("GPTZERO_API_KEY"):
        results["gptzero"] = gptzero(text)
    if not results:
        results["info"] = "No detector API keys found. Set GPTZERO_API_KEY."
    return results
