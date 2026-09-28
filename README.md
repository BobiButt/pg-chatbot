# PG User Manager Bot 🤖

> A conversational chatbot that manages users in a **PostgreSQL** database using
> natural language. No SQL to memorize — just type what you want.

Built with **Python**, **OpenRouter LLM**, and **Neon PostgreSQL**.

---

## 👋 About the Author

Hi, I'm **Mubeen Butt** — a web developer passionate about building tools that
make databases feel human-friendly.

- 🌐 Web developer
- 🐍 Python + PostgreSQL enthusiast
- 💡 I built this project to show how a small, local-first chatbot can manage
  real relational data without any heavy frameworks.

Feel free to connect or fork this project!

---

## 📖 About the Project

**PG User Manager Bot** lets you manage users in a PostgreSQL database through
**plain English** (or simple commands). Behind the scenes it:

1. Parses your message — first with a **fast local regex parser** (no API call),
   and only falls back to an **LLM** when the input is unusual.
2. Validates every field (name, address, CNIC, email, password).
3. Runs secure CRUD operations on PostgreSQL.
4. Enforces a **user / admin** permission model.

### ✨ Features

| Feature | Description |
|---------|-------------|
| 🗣️ Natural language | "register me, name Ali..." just works |
| ⚡ Local-first parser | 90% of commands never touch the network |
| 🧠 LLM fallback | Handles odd phrasing via OpenRouter |
| 🔐 Secure passwords | bcrypt hashing, never stored plain |
| 👑 Admin role | Promote users; admins can delete anyone |
| ✅ Validators | CNIC, email, password, name, address |
| 🗑️ Safe deletes | Every delete asks for confirmation |
| 📝 Logging | Actions logged to `chatbot.log` |
| ☁️ Cloud or local DB | Works with Neon cloud or local Postgres |

---

## 🚀 Quick Start

### 🐧 Linux / macOS

```bash
# 1. Clone the repo
git clone https://github.com/BobiButt/chatpg--PG-Chatbot-.git
cd chatpg--PG-Chatbot-

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file (see next section)
cp .env.example .env
nano .env

# 5. Initialise the DB (creates the users table)
python db.py

# 6. Run the bot
python chatbot.py
```

### 🪟 Windows (PowerShell)

```powershell
# 1. Clone the repo
git clone https://github.com/BobiButt/chatpg--PG-Chatbot-.git
cd chatpg--PG-Chatbot-

# 2. Create a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

#    If you get an execution policy error, run once:
#    Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
copy .env.example .env
notepad .env

# 5. Initialise the DB
python db.py

# 6. Run the bot
python chatbot.py
```

### 🪟 Windows (CMD)

```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
notepad .env
python db.py
python chatbot.py
```

> **Tip:** To leave the virtual environment later, just type `deactivate`.

---

## ⚙️ Configuration (`.env`)

Create a `.env` file in the project root with:

```env
# PostgreSQL / Neon
DB_HOST=your-db-host
DB_PORT=5432
DB_NAME=your-db-name
DB_USER=your-db-user
DB_PASSWORD=your-db-password

# OpenRouter (optional — only used as LLM fallback)
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=nvidia/nemotron-3-super-120b-a12b:free
```

> ⚠️ **Never commit `.env`.** It's already listed in `.gitignore`.

---

## 📦 Requirements

`requirements.txt`:

```
psycopg2-binary
python-dotenv
bcrypt
requests
```

Install with:

```bash
pip install -r requirements.txt
```

---

## 🎮 How to Use

Once `python chatbot.py` is running, you'll see:

```
============================================================
🤖 PG Chatbot — type 'help' to see commands, 'exit' to quit.
============================================================

You:
```

Just type what you want in natural language. Examples below.

---

## 📋 Command Reference

### 🔹 General

| Command | What it does |
|---------|--------------|
| `help` or `?` | Show the help menu |
| `whoami` | Show current login state (and admin flag) |
| `exit` / `quit` / `q` | Quit the chatbot |

### 🔹 Authentication

| Command | Example |
|---------|---------|
| Register | `register me, name Ali Khan, address 12 Main St Lahore, cnic 35202-1234567-1, email ali@test.com, password pass1234` |
| Login | `log me in as ali@test.com with password pass1234` |
| Logout | `logout` |

### 🔹 Profile

| Command | Example |
|---------|---------|
| Show your info | `show my info` |
| Update a field | `update my address to 99 New Road, Karachi` |
| Change password | `update my password to newpass456` |
| Verify by CNIC | `verify cnic 35202-1234567-1` |
| Verify by email | `verify email ali@test.com` |
| List all users | `list users` |

### 🔹 Delete

| Command | Who can run | Notes |
|---------|-------------|-------|
| `delete my account` | Logged-in user | Asks yes/no |
| `admin delete user <email>` | Admin only | Asks yes/no |

### 🔹 Chat

| Input | Response |
|-------|----------|
| `hi` / `hello` / `hey` / `salam` | Greeting |
| `thanks` / `thank you` | Friendly reply |
| `bye` / `goodbye` | Sign-off |

---

## ✅ Validation Rules

| Field | Rule |
|-------|------|
| **name** | Letters + spaces only, 2–100 characters |
| **address** | 5–255 characters |
| **cnic** | Format `12345-6789012-3` (13 digits, 5-7-1) |
| **email** | Standard email format |
| **password** | Min 8 characters, at least 1 letter + 1 digit |

---

## 🔐 Permissions

```
Anyone         → register, login, list users, verify, help
Logged in      → show my info, update my <field>, delete my account
Admin only     → admin delete user <email>
Admin rule     → cannot admin-delete yourself (use 'delete my account')
```

Every delete asks for **yes/no confirmation** before running.

---

## 🛠️ Admin Management (from Terminal)

### Promote a user to admin

```bash
python -c "
from db import get_connection
conn = get_connection(); cur = conn.cursor()
cur.execute(\"UPDATE users SET is_admin = TRUE WHERE email = 'user@example.com';\")
conn.commit(); print('Rows updated:', cur.rowcount)
cur.close(); conn.close()
"
```

### Demote an admin

```bash
python -c "
from db import get_connection
conn = get_connection(); cur = conn.cursor()
cur.execute(\"UPDATE users SET is_admin = FALSE WHERE email = 'user@example.com';\")
conn.commit(); print('Rows updated:', cur.rowcount)
cur.close(); conn.close()
"
```

### List all users with admin flag

```bash
python -c "
from db import get_connection
conn = get_connection(); cur = conn.cursor()
cur.execute('SELECT id, name, email, is_admin FROM users ORDER BY id;')
for r in cur.fetchall(): print(r)
cur.close(); conn.close()
"
```

### Count admins

```bash
python -c "
from db import get_connection
conn = get_connection(); cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM users WHERE is_admin = TRUE;')
print('Admins:', cur.fetchone()[0])
cur.close(); conn.close()
"
```

---

## 🆘 Recovery — If You Lock Yourself Out

### Recreate your admin account

```bash
python -c "
from auth import Session, register
s = Session()
print(register(s, 'Your Name', 'Your Address', '12345-1234567-1', 'you@example.com', 'pass1234'))
"
```

Then promote it to admin (use the "Promote a user" snippet above).

### Reset a user's password

```bash
python -c "
from db import get_connection
from security import hash_password
conn = get_connection(); cur = conn.cursor()
new_hash = hash_password('newpass1234')
cur.execute('UPDATE users SET password_hash = %s WHERE email = %s;', (new_hash, 'you@example.com'))
conn.commit(); print('Rows updated:', cur.rowcount)
cur.close(); conn.close()
"
```

### Force-logout a session

Just close and reopen the chatbot. Sessions are in-memory only.

---

## 📁 Project Structure

```
pg_chatbot/
├── chatbot.py         # Main loop + intent router
├── llm.py             # Local regex parser + OpenRouter fallback
├── auth.py            # Session, register, login, logout
├── crud.py            # DB operations (create/read/update/delete)
├── db.py              # PostgreSQL connection + init_db
├── security.py        # bcrypt hashing helpers
├── validators.py      # Input validation
├── .env               # Secrets (NOT committed)
├── .env.example       # Template for new users
├── .gitignore         # Excludes .env, venv/, __pycache__/, *.log
├── requirements.txt   # Python dependencies
├── README.md          # This file
└── chatbot.log        # Runtime log (auto-created)
```

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'psycopg2'` | Activate the venv: `source venv/bin/activate` (Linux) or `venv\Scripts\activate` (Windows) |
| `FATAL: password authentication failed` | Wrong `DB_PASSWORD` in `.env` |
| `psql: command not found` (Fedora) | `sudo dnf install postgresql` |
| `Rate limited (429)` | Local parser missed your input; rephrase using a documented command |
| `I couldn't parse that offline, and the LLM is unavailable` | Same as above; no API key or rate-limited |
| `Could not delete account` after admin-deleting yourself | Session is stale — restart the chatbot |
| Windows: `Activate.ps1 cannot be loaded` | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once |
| Windows: `python` not found | Install Python from [python.org](https://www.python.org/downloads/) and tick "Add to PATH" |

---

## 🗺️ Roadmap

- [x] Full CRUD via natural language
- [x] Local + LLM hybrid parser
- [x] Admin role & confirmation prompts
- [x] Logging
- [ ] Telegram wrapper
- [ ] Web UI (FastAPI + HTML)
- [ ] Docker image
- [ ] Unit tests (pytest)

---

## 📜 License

MIT — use it, fork it, ship it.

---

## 🙌 Acknowledgements

- [OpenRouter](https://openrouter.ai) — free LLM routing
- [Neon](https://neon.tech) — serverless PostgreSQL
- [bcrypt](https://pypi.org/project/bcrypt/) — password hashing

---

⭐ **If this project helped you, give it a star!**