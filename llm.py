import os
import json
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


SYSTEM_PROMPT = """You are an intent parser for a PostgreSQL user-management chatbot.

You MUST return ONE flat JSON object. NEVER nest objects. NEVER use markdown.
The top-level key "action" is ALWAYS a STRING.

Allowed actions:
- "register": needs name, address, cnic, email, password
- "login": needs email, password
- "logout"
- "read_self"
- "update": needs field (name/address/cnic/email/password), value
- "delete_self"
- "verify": needs cnic OR email
- "list_users"
- "help"
- "chat": needs message
- "admin_delete": needs email (admin only)
- "unknown"

Return ONLY the JSON object. Nothing else.
"""


KNOWN_ACTIONS = (
    "register", "login", "logout", "read_self",
    "update", "delete_self", "verify", "list_users",
    "help", "chat", "admin_delete", "unknown",
)


# ============================================================
# LOCAL PARSER (regex — no API call)
# ============================================================

def _grab(pattern: str, text: str, flags=0) -> str | None:
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


def parse_intent_local(msg: str) -> dict | None:
    m = msg.strip()
    low = m.lower()
    if not m:
        return None

    # greetings / chat / thanks / bye
    if re.fullmatch(r"(hi|hello|hey|salam|assalam[ou]?\s*alaikum|hola)[!., ]*", low):
        return {"action": "chat", "message": m}
    if re.fullmatch(r"(thanks?|thank\s*you|thx|shukriya)[!., ]*", low):
        return {"action": "chat", "message": m}
    if re.fullmatch(r"(bye|goodbye|see\s*ya|khuda\s*hafiz)[!., ]*", low):
        return {"action": "chat", "message": m}

    # help
    if re.search(r"\b(help|commands?|what can you do|options)\b", low):
        return {"action": "help"}

    # logout
    if re.search(r"\b(log\s*(me\s*)?out|sign\s*(me\s*)?out)\b", low):
        return {"action": "logout"}

    # list users
    if re.search(r"\b(list|show all|all)\s+users?\b", low):
        return {"action": "list_users"}

    # admin delete (must come BEFORE delete_self)
    if re.search(r"\b(admin\s+delete|delete\s+user|remove\s+user|ban\s+user)\b", low):
        email = _grab(r"([\w\.\-]+@[\w\.\-]+)", m, 0)
        if email:
            return {"action": "admin_delete", "email": email}
        return None

        # --- delete self (accepts: delete my account, delete me, remove me, ...) ---
    if re.search(r"\b(delete|remove|close)\b.*\b(my\s+)?(account|profile|me)\b", low):
        return {"action": "delete_self"}

    # show my info
    if re.search(r"\b(my\s+(info|data|profile|details|account)|show me|whoami|my info)\b", low):
        return {"action": "read_self"}
    

    # register
    if re.search(r"\b(register|sign\s*up|create\s+(an?\s+)?account|new\s+account)\b", low):
        fields = {
            "name":     _grab(r"name[:\s]+([A-Za-z ]+?)(?=\s*,\s*address|\s+address\b|$)", m, re.I),
            "address":  _grab(r"address[:\s]+(.+?)(?=\s*,\s*cnic|\s+cnic\b|\s*,\s*email|\s+email\b|\s*,\s*password|\s+password\b|$)", m, re.I),
            "cnic":     _grab(r"cnic[:\s]+([\d\-]+)", m, re.I),
            "email":    _grab(r"email[:\s]+([\w\.\-]+@[\w\.\-]+)", m, re.I),
            "password": _grab(r"(?:password|pass|pw)[:\s]+(\S+)", m, re.I),
        }
        cleaned = {k: v for k, v in fields.items() if v}
        if "name" in cleaned and len(cleaned) >= 2:
            return {"action": "register", **cleaned}
        return None

    # login
    if re.search(r"\b(log\s*(me\s*)?in|sign\s*(me\s*)?in)\b", low):
        email = _grab(r"([\w\.\-]+@[\w\.\-]+)", m, 0)
        pw    = _grab(r"(?:password|pass|pw)[:\s]+(\S+)", m, re.I)
        if email and pw:
            return {"action": "login", "email": email, "password": pw}
        return None

    # update
    if re.search(r"\b(update|change|set|edit|modify)\b", low):
        field = None
        for f in ("name", "address", "cnic", "email", "password"):
            if re.search(rf"\b{f}\b", low):
                field = f
                break
        value = _grab(r"\b(?:to|into)\s+(.+)$", m, re.I)
        if field and value:
            return {"action": "update", "field": field, "value": value.strip()}
        return None

    # verify
    if re.search(r"\b(verify|check|find|lookup|look\s*up|search)\b", low):
        cnic  = _grab(r"\b(\d{5}-\d{7}-\d)\b", m, 0)
        email = _grab(r"([\w\.\-]+@[\w\.\-]+)", m, 0)
        if cnic:
            return {"action": "verify", "cnic": cnic}
        if email:
            return {"action": "verify", "email": email}
        return None

    return None


# ============================================================
# CANNED CHAT (no API call)
# ============================================================

def chat_reply_local(msg: str) -> str:
    low = msg.lower()
    if re.search(r"\b(hi|hello|hey|salam|assalam|hola)\b", low):
        return "👋 Hi! I help you manage users in PostgreSQL. Type 'help' to see commands."
    if re.search(r"\b(thanks?|thank\s*you|thx|shukriya)\b", low):
        return "😊 You're welcome!"
    if re.search(r"\b(bye|goodbye|see\s*ya|khuda\s*hafiz)\b", low):
        return "👋 Bye! Come back anytime."
    return ("🤖 I'm a user-management bot. I can register, log in, update, "
            "verify, list users, or delete accounts. Type 'help'.")


# ============================================================
# LLM FALLBACK
# ============================================================

def _extract_json(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    end = -1
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == -1:
        return text[start:] + "}"
    return text[start:end + 1]


def _normalize(parsed: dict) -> dict:
    if not isinstance(parsed, dict) or not parsed:
        return {"action": "unknown"}
    action = parsed.get("action")
    if isinstance(action, dict):
        action_name = (
            action.get("name")
            or action.get("action")
            or next((k for k in action.keys() if k in KNOWN_ACTIONS), "unknown")
        )
        flattened = {"action": action_name}
        for k, v in action.items():
            if k in ("name", "action", action_name):
                continue
            flattened[k] = v
        for k, v in parsed.items():
            if k != "action":
                flattened[k] = v
        return flattened
    if action is None:
        for key in KNOWN_ACTIONS:
            if key in parsed:
                return {"action": key, **{k: v for k, v in parsed.items() if k != key}}
        return {"action": "unknown"}
    return parsed


def _call_openrouter(system: str, user: str, json_mode: bool = True) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
    if not api_key:
        return {"ok": False, "error": "OPENROUTER_API_KEY missing in .env"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "PG Chatbot",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3 if not json_mode else 0,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    last_error = None
    for attempt in range(3):
        try:
            r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
            if r.status_code == 429:
                wait = 2 ** attempt
                print(f"⏳ Rate limited. Retrying in {wait}s... (attempt {attempt + 1}/3)")
                time.sleep(wait)
                last_error = "Rate limited (429)"
                continue
            if r.status_code == 402:
                return {"ok": False, "error": "OpenRouter: insufficient credits (402)."}
            r.raise_for_status()
            data = r.json()
            if "choices" not in data or not data["choices"]:
                err = data.get("error", {})
                msg = err.get("message") if isinstance(err, dict) else str(err)
                return {"ok": False, "error": f"API returned no choices: {msg or data}"}
            content = data["choices"][0].get("message", {}).get("content")
            if not content:
                return {"ok": False, "error": "Empty content from model."}
            return {"ok": True, "content": content}
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return {"ok": False, "error": f"Network/API error: {e}"}
    return {"ok": False, "error": f"Failed after 3 attempts: {last_error}"}


# ============================================================
# PUBLIC FUNCTIONS
# ============================================================

def parse_intent(user_message: str) -> dict:
    # Local first
    local = parse_intent_local(user_message)
    if local is not None:
        return local

    # LLM fallback
    result = _call_openrouter(SYSTEM_PROMPT, user_message, json_mode=True)
    if not result["ok"]:
        return {"action": "llm_failed"}

    cleaned = _extract_json(result["content"])
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return {"action": "unknown"}
    return _normalize(parsed)


def chat_reply(user_message: str) -> str:
    return chat_reply_local(user_message)