"""
Flask application entry point for the Nutrition Agentic AI application.
"""

import uuid
import traceback
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from agents.nutrition_agent import NutritionAgent, STATE_PLAN
from agents.granite_client import GraniteAPIError

app = Flask(__name__)
app.secret_key = "nutri-ai-secret-2024-ibm-granite"
CORS(app)


@app.errorhandler(Exception)
def handle_unexpected_error(exc):
    """Return a clean JSON error for any unhandled exception instead of an HTML traceback."""
    tb = traceback.format_exc()
    app.logger.error("Unhandled exception:\n%s", tb)
    if isinstance(exc, GraniteAPIError):
        return jsonify({"error": str(exc)}), 502
    return jsonify({"error": f"Internal server error: {exc}"}), 500

# In-memory session store (keyed by session_id)
_sessions: dict[str, NutritionAgent] = {}


def _get_agent(session_id: str) -> NutritionAgent:
    if session_id not in _sessions:
        _sessions[session_id] = NutritionAgent()
    return _sessions[session_id]


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/session", methods=["POST"])
def new_session():
    """Create a new agent session and return its greeting."""
    sid   = str(uuid.uuid4())
    agent = _get_agent(sid)
    resp  = agent.process("")   # triggers STATE_INIT → greeting
    return jsonify({"session_id": sid, **resp})


@app.route("/api/chat", methods=["POST"])
def chat():
    """Send a user message to the agent and receive a response."""
    data       = request.get_json(force=True)
    sid        = data.get("session_id", "")
    user_input = data.get("message", "").strip()

    if not sid or sid not in _sessions:
        return jsonify({"error": "Invalid or expired session. Please refresh the page."}), 400

    agent = _get_agent(sid)

    # If the agent just collected location and needs to generate the plan
    if agent.state == STATE_PLAN:
        resp = agent.process("[GENERATE]")
    else:
        if not user_input:
            return jsonify({"error": "Message cannot be empty."}), 400
        resp = agent.process(user_input)

    return jsonify(resp)


@app.route("/api/generate_plan", methods=["POST"])
def generate_plan():
    """Explicitly trigger plan generation after profile collection."""
    data = request.get_json(force=True)
    sid  = data.get("session_id", "")

    if not sid or sid not in _sessions:
        return jsonify({"error": "Invalid session."}), 400

    agent = _get_agent(sid)
    resp  = agent.process("[GENERATE]")
    return jsonify(resp)


@app.route("/api/reset", methods=["POST"])
def reset_session():
    """Reset the agent session."""
    data = request.get_json(force=True)
    sid  = data.get("session_id", "")
    if sid in _sessions:
        del _sessions[sid]
    new_sid   = str(uuid.uuid4())
    new_agent = _get_agent(new_sid)
    resp      = new_agent.process("")
    return jsonify({"session_id": new_sid, **resp})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "model": "ibm/granite-4-h-small"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
