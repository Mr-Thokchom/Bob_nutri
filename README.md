# 🌿 NutriBot — AI Nutrition Assistant

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask&logoColor=white)
![IBM Granite](https://img.shields.io/badge/IBM%20Granite-4--h--small-0f62fe?logo=ibm&logoColor=white)
![watsonx.ai](https://img.shields.io/badge/watsonx.ai-EU--DE-be95ff?logo=ibm&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

**A web-based Agentic AI application that collects your personal health profile and generates a personalized 7-day nutrition plan using IBM Granite on watsonx.ai.**

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [API Reference](#-api-reference) · [AI Ethics](#️-ai-ethics--guardrails) · [Disclaimer](#️-medical-disclaimer)

</div>

---

## ✨ Features

- 🤖 **Agentic conversation** — guided multi-turn chat to collect name, age, diet preference, medical history, and location
- 🥗 **Personalized 7-day meal plan** — breakfast, snacks, lunch, and dinner tailored to your profile
- 🌍 **Location-aware** — uses locally available foods based on your city and country
- 💬 **Open Q&A chat** — ask follow-up nutrition questions after your plan is generated
- 🛡️ **Built-in guardrails** — blocks harmful content, refuses medical prescriptions, validates all inputs
- ⚖️ **HAM tone** — Helpful, Accurate, Mindful communication throughout
- 📄 **Plan export** — print or copy your nutrition plan to clipboard
- 📱 **Responsive UI** — works on desktop, tablet, and mobile

---

## 🏗️ Architecture

```
nutrition-ai/
├── app.py                    # Flask REST API (6 endpoints)
├── requirements.txt          # Python dependencies
├── run.bat                   # Windows launcher
├── run.sh                    # Linux / macOS launcher
├── agents/
│   ├── granite_client.py     # IBM watsonx.ai Chat API client (IAM auth + token cache)
│   ├── nutrition_agent.py    # Stateful agentic conversation engine (state machine)
│   └── guardrails.py         # AI ethics, safety rules, HAM tone, medical disclaimer
├── templates/
│   └── index.html            # Jinja2 web UI template
└── static/
    ├── css/style.css         # Application stylesheet (responsive)
    └── js/app.js             # Frontend agentic conversation controller
```

### Agentic Conversation Flow

```
START
 └─ Greet user
     └─ Collect Name
         └─ Collect Age (validated 1–120)
             └─ Collect Diet  (Veg / Non-Veg / Vegan / Pescatarian)
                 └─ Collect Medical History
                     └─ Collect Location (City, Country)
                         └─ ⚡ IBM Granite generates 7-Day Nutrition Plan
                             └─ Open Q&A Chat (follow-up questions)
```

---

## 🚀 Quick Start

### Prerequisites

- Python **3.9 or higher**
- `pip` package manager
- An IBM Cloud account with a watsonx.ai project (credentials below)

### 1. Clone the repository

```bash
git clone https://github.com/Mr-Thokchom/Bob_nutri.git
cd Bob_nutri
```

### 2. Create a virtual environment (recommended)

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure IBM Granite credentials

The app ships with a default configuration. To use your own credentials, set these environment variables **before** running:

```bash
# macOS / Linux
export IBM_PROJECT_ID="your-project-id"
export IBM_ENDPOINT_URL="https://eu-de.ml.cloud.ibm.com"
export IBM_API_KEY="your-api-key"

# Windows PowerShell
$env:IBM_PROJECT_ID="your-project-id"
$env:IBM_ENDPOINT_URL="https://eu-de.ml.cloud.ibm.com"
$env:IBM_API_KEY="your-api-key"
```

Or create a `.env` file in the project root:

```env
IBM_PROJECT_ID=your-project-id
IBM_ENDPOINT_URL=https://eu-de.ml.cloud.ibm.com
IBM_API_KEY=your-api-key
```

### 5. Run the application

**Windows:**
```
run.bat
```

**macOS / Linux:**
```bash
chmod +x run.sh && ./run.sh
```

**Directly:**
```bash
python app.py
```

### 6. Open in browser

```
http://localhost:5000
```

---

## 🤖 IBM Granite Configuration

| Setting         | Value                                        |
|-----------------|----------------------------------------------|
| **Model**       | `ibm/granite-4-h-small`                      |
| **API Version** | `2023-05-29`                                 |
| **Endpoint**    | `https://eu-de.ml.cloud.ibm.com`             |
| **Auth**        | IBM Cloud IAM — API Key → Bearer token       |
| **Token cache** | Automatically cached, refreshed before expiry|
| **Plan tokens** | Up to 2048 new tokens                        |
| **Chat tokens** | Up to 512 new tokens                         |

---

## 📡 API Reference

| Method | Endpoint              | Body (JSON)                                | Description                        |
|--------|-----------------------|--------------------------------------------|------------------------------------|
| `GET`  | `/`                   | —                                          | Serve the web UI                   |
| `POST` | `/api/session`        | `{}`                                       | Create a new agent session         |
| `POST` | `/api/chat`           | `{"session_id": "...", "message": "..."}`  | Send message, receive agent reply  |
| `POST` | `/api/generate_plan`  | `{"session_id": "..."}`                    | Trigger nutrition plan generation  |
| `POST` | `/api/reset`          | `{"session_id": "..."}`                    | Reset session, start fresh         |
| `GET`  | `/health`             | —                                          | Health check                       |

### Example: Start a session

```bash
curl -X POST http://localhost:5000/api/session \
     -H "Content-Type: application/json" \
     -d '{}'
```

### Example: Send a message

```bash
curl -X POST http://localhost:5000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"session_id": "<your-session-id>", "message": "John Doe"}'
```

---

## 🛡️ AI Ethics & Guardrails

NutriBot is designed with responsible AI principles baked in:

| Guardrail | Behaviour |
|-----------|-----------|
| **Harmful content** | Blocks self-harm, eating disorders, crash diets — returns a compassionate redirect |
| **Prescription requests** | Refuses to diagnose conditions or prescribe medications |
| **Age validation** | Accepts only ages 1–120 |
| **Input sanitization** | Strips and length-caps all user inputs before processing |
| **HAM tone** | All LLM prompts enforce Helpful, Accurate, Mindful communication |
| **Medical disclaimer** | Automatically appended to every generated nutrition plan |
| **Error transparency** | API failures surface as human-readable messages, never raw tracebacks |

---

## 🗂️ Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| LLM         | IBM Granite 4h Small via watsonx.ai |
| Backend     | Python 3.9+ · Flask 3.0             |
| Frontend    | Vanilla HTML5 · CSS3 · JavaScript   |
| Auth        | IBM Cloud IAM (API Key)             |
| HTTP client | `requests`                          |

---

## ⚕️ Medical Disclaimer

> This application is for **general wellness and informational purposes only.**
> It is **not** a substitute for professional medical advice, diagnosis, or treatment.
> Always consult a qualified healthcare provider or registered dietitian before making
> significant changes to your diet, especially if you have a medical condition.
> Never disregard professional medical advice because of something you have read here.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
Built with ❤️ using <strong>IBM Granite</strong> on <strong>watsonx.ai</strong>
</div>
