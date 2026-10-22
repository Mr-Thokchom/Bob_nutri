"""
Nutrition Agent — agentic orchestration layer.
Handles multi-turn conversation state, prompt construction,
and tool-like reasoning steps for personalized nutrition planning.
"""

from agents.granite_client import generate_text, GraniteAPIError
from agents.guardrails import (
    contains_harmful_content,
    contains_prescription_request,
    validate_age,
    sanitize_input,
    get_harmful_response,
    get_prescription_response,
    append_disclaimer,
)

# ─── Conversation states ───────────────────────────────────────────────────────
STATE_INIT      = "init"
STATE_NAME      = "collect_name"
STATE_AGE       = "collect_age"
STATE_DIET      = "collect_diet"
STATE_MEDICAL   = "collect_medical"
STATE_LOCATION  = "collect_location"
STATE_PLAN      = "generate_plan"
STATE_CHAT      = "chat"

DIET_OPTIONS = {"1": "vegetarian", "2": "non-vegetarian", "3": "vegan", "4": "pescatarian"}


def _build_plan_prompt(user: dict) -> str:
    return f"""You are NutriBot, a compassionate and knowledgeable AI nutrition assistant.
You follow HAM (Helpful, Accurate, Mindful) communication principles.
You respect the user's culture, preferences, and medical background.

Generate a detailed, personalized 7-day nutrition plan for the following individual:

Name        : {user['name']}
Age         : {user['age']}
Diet Type   : {user['diet']}
Medical     : {user['medical'] or 'None reported'}
Location    : {user['city']}, {user['country']}

Instructions:
- Structure the plan as Day 1 through Day 7.
- Each day must have Breakfast, Mid-Morning Snack, Lunch, Afternoon Snack, and Dinner.
- Include portion guidance (e.g., "1 cup", "100g").
- Incorporate locally available foods appropriate for {user['city']}, {user['country']}.
- Adjust for medical conditions: {user['medical'] or 'none'}.
- Keep calorie balance appropriate for age {user['age']} with a {user['diet']} diet.
- Use a warm, encouraging, and respectful tone throughout.
- After the 7-day plan, add a "Hydration & Lifestyle Tips" section.
- Do NOT recommend medications or act as a doctor.
- Begin directly with the plan. Do not repeat the user's details back.
"""


def _build_chat_prompt(user: dict, history: list, user_message: str) -> str:
    history_text = ""
    for turn in history[-6:]:  # keep last 6 turns for context window
        history_text += f"User: {turn['user']}\nNutriBot: {turn['bot']}\n"

    return f"""You are NutriBot, a compassionate AI nutrition assistant using HAM communication.
You help users with nutrition questions, healthy recipes, meal ideas, and wellness tips.
You do NOT diagnose conditions, prescribe medicine, or give dosages.
You always recommend consulting a healthcare professional for medical concerns.

User Profile: {user.get('name', 'User')}, Age {user.get('age', 'unknown')},
Diet: {user.get('diet', 'unknown')}, Medical: {user.get('medical', 'none')},
Location: {user.get('city', '')}, {user.get('country', '')}

Conversation history:
{history_text}
User: {user_message}
NutriBot:"""


class NutritionAgent:
    """
    Stateful agentic AI session for one user.
    Manages conversation flow, data collection, and LLM calls.
    """

    def __init__(self):
        self.state   = STATE_INIT
        self.user    = {}
        self.history = []  # list of {"user": ..., "bot": ...}

    # ── Public entry point ───────────────────────────────────────────────────

    def process(self, user_input: str) -> dict:
        """
        Accept user input, advance agent state, return response dict:
        {
            "message": str,          # bot response text
            "state": str,            # current state label
            "plan_ready": bool,      # True when nutrition plan is generated
            "user_profile": dict,    # collected profile (once complete)
        }
        """
        user_input = sanitize_input(user_input)

        # ── Global guardrail checks ──────────────────────────────────────────
        if contains_harmful_content(user_input):
            return self._reply(get_harmful_response())

        if contains_prescription_request(user_input) and self.state == STATE_CHAT:
            return self._reply(get_prescription_response())

        # ── Route by state ───────────────────────────────────────────────────
        if self.state == STATE_INIT:
            return self._handle_init()

        if self.state == STATE_NAME:
            return self._handle_name(user_input)

        if self.state == STATE_AGE:
            return self._handle_age(user_input)

        if self.state == STATE_DIET:
            return self._handle_diet(user_input)

        if self.state == STATE_MEDICAL:
            return self._handle_medical(user_input)

        if self.state == STATE_LOCATION:
            return self._handle_location(user_input)

        if self.state == STATE_PLAN:
            return self._handle_generate_plan()

        if self.state == STATE_CHAT:
            return self._handle_chat(user_input)

        return self._reply("I'm not sure how to handle that. Let's start over.", reset=True)

    # ── State handlers ───────────────────────────────────────────────────────

    def _handle_init(self) -> dict:
        self.state = STATE_NAME
        msg = (
            "👋 Hello! I'm **NutriBot**, your personal AI nutrition assistant powered by IBM Granite.\n\n"
            "I'll help you create a **personalized 7-day nutrition plan** based on your unique profile.\n\n"
            "Let's get started! 🌿\n\n"
            "**What is your full name?**"
        )
        return self._reply(msg)

    def _handle_name(self, value: str) -> dict:
        if len(value) < 2:
            return self._reply("Please enter a valid name (at least 2 characters).")
        self.user["name"] = value.title()
        self.state = STATE_AGE
        return self._reply(f"Nice to meet you, **{self.user['name']}**! 😊\n\n**How old are you?** (Please enter your age in years)")

    def _handle_age(self, value: str) -> dict:
        ok, err = validate_age(value)
        if not ok:
            return self._reply(f"⚠️ {err} Please try again.")
        self.user["age"] = int(value)
        self.state = STATE_DIET
        return self._reply(
            "Got it! 🎂\n\n**What is your diet preference?**\n\n"
            "1️⃣ Vegetarian\n"
            "2️⃣ Non-Vegetarian\n"
            "3️⃣ Vegan\n"
            "4️⃣ Pescatarian\n\n"
            "Please type the number or the name of your preference."
        )

    def _handle_diet(self, value: str) -> dict:
        choice = value.strip().lower()
        if choice in DIET_OPTIONS:
            diet = DIET_OPTIONS[choice]
        elif choice in DIET_OPTIONS.values():
            diet = choice
        else:
            # fuzzy match
            for k, v in DIET_OPTIONS.items():
                if v.startswith(choice[:3]):
                    diet = v
                    break
            else:
                return self._reply(
                    "I didn't catch that. Please choose:\n"
                    "1 - Vegetarian | 2 - Non-Vegetarian | 3 - Vegan | 4 - Pescatarian"
                )
        self.user["diet"] = diet
        self.state = STATE_MEDICAL
        return self._reply(
            f"Great choice — **{diet.capitalize()}** diet noted! 🥗\n\n"
            "**Do you have any medical conditions I should consider?**\n"
            "*(e.g., diabetes, high blood pressure, thyroid, cholesterol, PCOS, kidney disease)*\n\n"
            "If none, just type **'None'** or **'No'**."
        )

    def _handle_medical(self, value: str) -> dict:
        v = value.strip().lower()
        self.user["medical"] = "" if v in ("none", "no", "n/a", "-", "nil") else value
        self.state = STATE_LOCATION
        return self._reply(
            "Thank you for sharing that. 🩺\n\n"
            "**Where are you located?**\n"
            "Please enter your **City** and **Country** (e.g., *Mumbai, India* or *Berlin, Germany*)"
        )

    def _handle_location(self, value: str) -> dict:
        parts = [p.strip() for p in value.split(",")]
        if len(parts) < 2:
            return self._reply(
                "Please enter both your city and country separated by a comma.\n"
                "Example: *London, United Kingdom*"
            )
        self.user["city"]    = parts[0].title()
        self.user["country"] = ", ".join(parts[1:]).title()
        self.state           = STATE_PLAN
        summary = (
            f"✅ **Profile Complete!**\n\n"
            f"| Field | Details |\n"
            f"|---|---|\n"
            f"| **Name** | {self.user['name']} |\n"
            f"| **Age** | {self.user['age']} |\n"
            f"| **Diet** | {self.user['diet'].capitalize()} |\n"
            f"| **Medical** | {self.user['medical'] or 'None'} |\n"
            f"| **Location** | {self.user['city']}, {self.user['country']} |\n\n"
            "🔄 Generating your personalized 7-day nutrition plan... Please wait a moment."
        )
        return self._reply(summary, trigger_plan=True)

    def _handle_generate_plan(self) -> dict:
        prompt = _build_plan_prompt(self.user)
        try:
            raw_plan = generate_text(prompt, max_tokens=2048, temperature=0.6)
        except GraniteAPIError as exc:
            # Stay in STATE_PLAN so the user can retry
            return self._reply(
                f"⚠️ **I couldn't generate your plan right now.**\n\n"
                f"_Error: {exc}_\n\n"
                "Please click **Generate Plan** again or refresh the page to retry."
            )
        plan = append_disclaimer(raw_plan)
        self.state = STATE_CHAT
        self.history.append({"user": "[PLAN GENERATED]", "bot": plan})
        return self._reply(plan, plan_ready=True)

    def _handle_chat(self, user_input: str) -> dict:
        prompt = _build_chat_prompt(self.user, self.history, user_input)
        try:
            response = generate_text(prompt, max_tokens=512, temperature=0.7)
        except GraniteAPIError as exc:
            return self._reply(
                f"⚠️ **Something went wrong while contacting the AI.**\n\n"
                f"_Error: {exc}_\n\nPlease try again."
            )
        self.history.append({"user": user_input, "bot": response})
        return self._reply(response)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _reply(self, message: str, reset: bool = False,
               trigger_plan: bool = False, plan_ready: bool = False) -> dict:
        if reset:
            self.state = STATE_INIT
        return {
            "message":      message,
            "state":        self.state,
            "trigger_plan": trigger_plan,
            "plan_ready":   plan_ready,
            "user_profile": self.user if self.state in (STATE_PLAN, STATE_CHAT) else {},
        }
