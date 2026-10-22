"""
IBM Granite LLM client — wraps the watsonx.ai Chat API.
Uses ibm/granite-4-h-small via the /ml/v1/text/chat endpoint.
"""

import os
import time
import requests

# ─── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ID   = os.getenv("IBM_PROJECT_ID",   "b6cb73ad-7586-4b7a-b101-b680d376cfdf")
ENDPOINT_URL = os.getenv("IBM_ENDPOINT_URL", "https://eu-de.ml.cloud.ibm.com")
API_KEY      = os.getenv("IBM_API_KEY",      "kaCkLh2ce-yo5hxFQgGW4_9xu0V3Mo5bnF5I6ZqF_vB7")

IAM_URL      = "https://iam.cloud.ibm.com/identity/token"
MODEL_ID     = "ibm/granite-4-h-small"          # available & tested on eu-de

_cached_token: dict = {}


def _get_iam_token() -> str:
    """Fetch (or return cached) IBM Cloud IAM bearer token."""
    now = time.time()
    if _cached_token.get("token") and now < _cached_token.get("expires_at", 0) - 60:
        return _cached_token["token"]

    resp = requests.post(
        IAM_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey":     API_KEY,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    _cached_token["token"]      = data["access_token"]
    _cached_token["expires_at"] = now + int(data.get("expires_in", 3600))
    return _cached_token["token"]


def generate_text(prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
    """
    Call the watsonx.ai /text/chat endpoint with IBM Granite and return
    the assistant's reply as a plain string.

    Raises GraniteAPIError with a human-readable message on any failure.
    """
    try:
        token = _get_iam_token()
    except requests.RequestException as exc:
        raise GraniteAPIError(f"IAM authentication failed: {exc}") from exc

    url = f"{ENDPOINT_URL}/ml/v1/text/chat?version=2023-05-29"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }
    payload = {
        "model_id":   MODEL_ID,
        "project_id": PROJECT_ID,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "parameters": {
            "max_tokens":   max_tokens,
            "temperature":  temperature,
        },
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
    except requests.RequestException as exc:
        raise GraniteAPIError(f"Network error contacting watsonx.ai: {exc}") from exc

    if not resp.ok:
        # Extract the IBM error message if available
        try:
            errors = resp.json().get("errors", [])
            msg = errors[0]["message"] if errors else resp.text[:300]
        except Exception:
            msg = resp.text[:300]
        raise GraniteAPIError(f"watsonx.ai API error ({resp.status_code}): {msg}")

    try:
        result = resp.json()
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, ValueError) as exc:
        raise GraniteAPIError(f"Unexpected response shape from watsonx.ai: {exc}") from exc


class GraniteAPIError(Exception):
    """Raised when the Granite / watsonx.ai API call fails."""
