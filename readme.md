# pg-user-manager-bot

A conversational chatbot that manages users in a PostgreSQL database 
using natural language. Built with Python, OpenRouter LLM, and Neon PostgreSQL.

## Features
- Natural-language commands (no syntax to memorize)
- Local regex parser (fast, no API calls) with LLM fallback
- Full CRUD on users (register, update, verify, delete)
- Admin role with privilege escalation
- bcrypt password hashing
- Works with any PostgreSQL (local or Neon cloud)

## Quick Start
================================================================
PG CHATBOT — FULL COMMAND REFERENCE
================================================================
Last updated: 2026
Project folder: ~/Desktop/Python projects/hccda/pg_chatbot
================================================================

------------------------------------------------
1. STARTING THE BOT
------------------------------------------------

# From terminal, inside the project folder:
cd ~/Desktop/Python\ projects/hccda/pg_chatbot
source venv/bin/activate
python chatbot.py

# When done:
deactivate                      # leave the venv

# One-liner shortcut (add to ~/.bashrc once):
alias pgchat="cd ~/Desktop/Python\ projects/hccda/pg_chatbot && source venv/bin/activate && python chatbot.py"
# Then just type:
pgchat

------------------------------------------------
2. IN-CHAT COMMANDS (type these in the chatbot)
------------------------------------------------

GENERAL
  help                             Show help menu
  ?                                Same as help
  whoami                           Show current login state (and admin flag)
  exit / quit / q                  Quit the chatbot

AUTH / SESSION
  register me, name <name>, address <addr>, cnic <cnic>, email <email>, password <pass>
  log me in as <email> with password <pass>
  logout

PROFILE
  show my info                     Show your own record
  update my <field> to <value>     Update: name, address, cnic, email, or password
  verify cnic <cnic>               Look up a user by CNIC
  verify email <email>             Look up a user by email
  list users                       List all users (admin 👑 badge shown)

DELETE
  delete my account                Delete YOUR OWN account (asks yes/no)
  delete me                        Same as above
  admin delete user <email>        (Admin only) Delete any user (asks yes/no)

CHAT / GREETINGS
  hi / hello / hey / salam
  thanks / thank you
  bye / goodbye

------------------------------------------------
3. VALIDATION RULES
------------------------------------------------

  name     : letters + spaces only, 2–100 chars
  address  : 5–255 chars
  cnic     : 12345-6789012-3  (13 digits, 5-7-1 with dashes)
  email    : standard format (user@domain.tld)
  password : min 8 chars, must have 1 letter + 1 digit

------------------------------------------------
4. PERMISSIONS
------------------------------------------------

  Anyone         : register, login, list users, verify, help
  Logged in      : show my info, update my <field>, delete my account
  Admin only     : admin delete user <email>
  Admin rule     : cannot admin-delete yourself (use 'delete my account')

  Every delete (self or admin) asks for yes/no confirmation.

------------------------------------------------
5. ADMIN MANAGEMENT (run in terminal, not in chat)
------------------------------------------------

# Promote any user to admin:
python -c "
from db import get_connection
conn = get_connection(); cur = conn.cursor()
cur.execute(\"UPDATE users SET is_admin = TRUE WHERE email = 'user@example.com';\")
conn.commit(); print('Rows updated:', cur.rowcount)
cur.close(); conn.close()
"

# Demote an admin back to normal:
python -c "
from db import get_connection
conn = get_connection(); cur = conn.cursor()
cur.execute(\"UPDATE users SET is_admin = FALSE WHERE email = 'user@example.com';\")
conn.commit(); print('Rows updated:', cur.rowcount)
cur.close(); conn.close()
"

# List all users with admin flag:
python -c "
from db import get_connection
conn = get_connection(); cur = conn.cursor()
cur.execute('SELECT id, name, email, is_admin FROM users ORDER BY id;')
for r in cur.fetchall(): print(r)
cur.close(); conn.close()
"

# Count admins:
python -c "
from db import get_connection
conn = get_connection(); cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM users WHERE is_admin = TRUE;')
print('Admins:', cur.fetchone()[0])
cur.close(); conn.close()
"

------------------------------------------------
6. RECOVERY (if you lock yourself out)
------------------------------------------------

# Re-create your admin account (if you deleted it):
python -c "
from auth import Session, register
s = Session()
print(register(s, 'Your Name', 'Your Address', '12345-1234567-1', 'you@example.com', 'pass1234'))
"

# Then promote it to admin:
python -c "
from db import get_connection
conn = get_connection(); cur = conn.cursor()
cur.execute(\"UPDATE users SET is_admin = TRUE WHERE email = 'you@example.com';\")
conn.commit(); print('Rows updated:', cur.rowcount)
cur.close(); conn.close()
"

# Reset a user's password (from terminal):
python -c "
from db import get_connection
from security import hash_password
conn = get_connection(); cur = conn.cursor()
new_hash = hash_password('newpass1234')
cur.execute('UPDATE users SET password_hash = %s WHERE email = %s;', (new_hash, 'you@example.com'))
conn.commit(); print('Rows updated:', cur.rowcount)
cur.close(); conn.close()
"

# Force-logout a session: just close and reopen the chatbot.

------------------------------------------------
7. FIRST-TIME SETUP (fresh machine)
------------------------------------------------

1. cd ~/Desktop/Python\ projects/hccda/pg_chatbot
2. python -m venv venv
3. source venv/bin/activate
4. pip install psycopg2-binary python-dotenv bcrypt requests
5. Ensure .env exists with:
     DB_HOST=...
     DB_PORT=5432
     DB_NAME=neondb
     DB_USER=neondb_owner
     DB_PASSWORD=...
     OPENROUTER_API_KEY=sk-or-v1-...        # optional (fallback only)
     OPENROUTER_MODEL=nvidia/nemotron-3-super-120b-a12b:free
6. python db.py                # creates/verifies users table
7. python chatbot.py           # runs the bot

------------------------------------------------
8. FILES IN THE PROJECT
------------------------------------------------

  db.py             PostgreSQL connection + init_db (creates users table)
  security.py       bcrypt hashing (hash_password, verify_password)
  validators.py     Input validation (name, address, cnic, email, password)
  crud.py           Database operations (create/read/update/delete)
  auth.py           Session class + register/login/logout
  llm.py            Local regex parser + OpenRouter LLM fallback
  chatbot.py        Main loop + intent router
  .env              Secrets (DB creds, OpenRouter key) — DO NOT SHARE
  .gitignore        Should contain: .env, venv/, __pycache__/, chatbot.log
  chatbot.log       Runtime log (created on first run)

------------------------------------------------
9. TROUBLESHOOTING
------------------------------------------------

# ModuleNotFoundError: No module named 'psycopg2'
  → venv not activated. Run: source venv/bin/activate

# FATAL: password authentication failed
  → Wrong DB_PASSWORD in .env, or psql got literal placeholder text

# Rate limited (429) messages
  → Local parser didn't match your input, LLM hit the free-tier cap.
    Rephrase using a command from Section 2.

# 💡 I couldn't parse that offline, and the LLM is unavailable
  → Same cause. Local parser missed it and LLM is rate-limited / no key.

# psql: command not found (on Fedora)
  → sudo dnf install postgresql

# "Could not delete account" after admin-deleting yourself
  → Account already gone. The session is stale.
    Do: close and reopen the chatbot (this restarts the session).

# Need to reset a forgotten admin password
  → See Section 6 above.

------------------------------------------------
10. EXAMPLE END-TO-END FLOW
------------------------------------------------

You: register me, name Ali Khan, address 12 Main St Lahore, cnic 35202-1234567-1, email ali@test.com, password pass1234
Bot: ✅ Registered & logged in as Ali Khan (id=1).

You: show my info
Bot: 📋 Your info:
       id: 1
       name: Ali Khan
       ...

You: update my address to 99 New Road, Karachi
Bot: ✅ Updated. New info: ...

You: logout
Bot: 👋 Goodbye, Ali Khan. You have been logged out.

You: log me in as ali@test.com with password pass1234
Bot: ✅ Welcome back, Ali Khan!

You: delete my account
Bot: ⚠️  Are you sure you want to DELETE your account (Ali Khan)? (yes/no): yes
Bot: 🗑️ Account for Ali Khan deleted. You have been logged out.

You: exit
Bot: 👋 Bye!

================================================================
END OF REFERENCE
================================================================