import logging

from llm import parse_intent, chat_reply
from auth import Session, register, login, logout
from crud import (
    get_user_by_id,
    get_user_by_cnic,
    get_user_by_email,
    update_user_field,
    delete_user,
    delete_user_by_email,
    list_users,
)
from validators import (
    validate_name, validate_address, validate_cnic,
    validate_email, validate_password,
)


# ---------- LOGGING ----------
logging.basicConfig(
    filename="chatbot.log",
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def log(msg: str):
    logging.info(msg)


# ---------- TEXT ----------
HELP_TEXT = """
🤖 PG Chatbot — available commands:

  • register me, name <name>, address <addr>, cnic <cnic>, email <email>, password <pass>
  • log me in as <email> with password <pass>
  • show my info
  • update my <field> to <new value>
  • verify cnic <cnic>   |   verify email <email>
  • list users
  • logout

  Admin only:
  • admin delete user <email>

  • help | exit
"""


def fmt_user(u: dict) -> str:
    tag = "  👑 ADMIN" if u.get("is_admin") else ""
    return (
        f"  id:      {u['id']}\n"
        f"  name:    {u['name']}\n"
        f"  address: {u['address']}\n"
        f"  cnic:    {u['cnic']}\n"
        f"  email:   {u['email']}"
        f"{tag}"
    )


def confirm(prompt: str) -> bool:
    while True:
        ans = input(f"{prompt} (yes/no): ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no", ""):
            return False
        print("   Please answer 'yes' or 'no'.")


# ---------- HANDLER ----------
def handle_intent(intent: dict, session: Session) -> str:
     # Sanity check — if logged in but the account no longer exists, force logout
    if session.is_logged_in:
        existing = get_user_by_id(session.user_id)
        if not existing:
            session.logout()
    action = intent.get("action")

    if action in ("help", "unknown"):
        return HELP_TEXT.strip()
    if action == "llm_failed":
        return ("🤖 I couldn't parse that offline, and the LLM is unavailable "
                "(rate limit or missing key). Try rephrasing, or type 'help'.")

    if action == "error":
        return f"⚠️ {intent.get('message', 'Unknown error')}"

    if action == "chat":
        return chat_reply(intent.get("message") or intent.get("text") or "")

    # REGISTER
    if action == "register":
        ok, msg = register(
            session,
            intent.get("name", ""),
            intent.get("address", ""),
            intent.get("cnic", ""),
            intent.get("email", ""),
            intent.get("password", ""),
        )
        return msg

    # LOGIN
    if action == "login":
        if session.is_logged_in:
            return f"⚠️ Already logged in as {session.user['name']}. Logout first."
        ok, msg = login(session, intent.get("email", ""), intent.get("password", ""))
        return msg

    # LOGOUT
    if action == "logout":
        ok, msg = logout(session)
        return msg

    # READ SELF
    if action == "read_self":
        if not session.is_logged_in:
            return "❌ You must be logged in. Try: 'log me in as <email> with password <pass>'"
        fresh = get_user_by_id(session.user_id)
        if not fresh:
            session.logout()
            return "⚠️ Your account no longer exists. Logged out."
        return "📋 Your info:\n" + fmt_user(fresh)

    # UPDATE
    if action == "update":
        if not session.is_logged_in:
            return "❌ You must be logged in to update."
        field = intent.get("field", "").strip().lower()
        value = intent.get("value", "").strip()

        validators = {
            "name": validate_name, "address": validate_address,
            "cnic": validate_cnic, "email": validate_email,
            "password": validate_password,
        }
        if field not in validators:
            return f"❌ Cannot update '{field}'. Allowed: name, address, cnic, email, password."

        ok, cleaned = validators[field](value)
        if not ok:
            return f"❌ {cleaned}"

        db_field = "password_hash" if field == "password" else field
        result = update_user_field(session.user_id, db_field, cleaned)
        if "error" in result:
            err = result["error"].lower()
            if "users_email_key" in err:
                return "❌ That email is already registered to another account."
            if "users_cnic_key" in err:
                return "❌ That CNIC is already registered to another account."
            return f"⚠️ Update failed: {result['error']}"

        session.login(result)
        log(f"UPDATE | user={session.user_id} | field={field}")
        return "✅ Updated. New info:\n" + fmt_user(result)

    # DELETE SELF (with confirm)
        # DELETE SELF
    if action == "delete_self":
        if not session.is_logged_in:
            return "❌ You must be logged in to delete your account."
        name = session.user["name"]
        if not confirm(f"⚠️  Are you sure you want to DELETE your account ({name})?"):
            return "↩️ Deletion cancelled."
        if delete_user(session.user_id):
            session.logout()
            log(f"DELETE_SELF | user={name}")
            return f"🗑️ Account for {name} deleted. You have been logged out."
        # Row already gone → still logout
        session.logout()
        return f"⚠️ Account already deleted. You have been logged out."

    # ADMIN DELETE
        # ADMIN DELETE
    if action == "admin_delete":
        if not session.is_logged_in:
            return "❌ You must be logged in as admin."
        if not session.user.get("is_admin"):
            return "❌ Admin only. You don't have permission."
        target_email = intent.get("email", "").strip().lower()
        if not target_email:
            return "❌ Provide an email. Example: 'admin delete user john@x.com'"
        if target_email == session.user["email"].lower():
            return ("❌ You can't admin-delete yourself. Use 'delete my account' instead "
                    "(which asks for confirmation).")
        target = get_user_by_email(target_email)
        if not target:
            return f"❌ No user found with email {target_email}."
        if not confirm(f"⚠️  Admin: DELETE user {target['name']} ({target_email})?"):
            return "↩️ Deletion cancelled."
        if delete_user_by_email(target_email):
            log(f"ADMIN_DELETE | admin={session.user['name']} | target={target_email}")
            return f"🗑️ User {target['name']} ({target_email}) deleted."
        return "⚠️ Could not delete user."

    # VERIFY
    if action == "verify":
        cnic = intent.get("cnic")
        email = intent.get("email")
        if cnic:
            ok, cleaned = validate_cnic(cnic)
            if not ok:
                return f"❌ {cleaned}"
            user = get_user_by_cnic(cleaned)
        elif email:
            ok, cleaned = validate_email(email)
            if not ok:
                return f"❌ {cleaned}"
            user = get_user_by_email(cleaned)
        else:
            return "❌ Provide 'cnic' or 'email' to verify."
        if not user:
            return "❌ No user found with that identifier."
        user.pop("password_hash", None)
        return "✅ User found:\n" + fmt_user(user)

    # LIST USERS
    if action == "list_users":
        users = list_users()
        if not users:
            return "📭 No users registered yet."
        lines = []
        for u in users:
            tag = " 👑" if u.get("is_admin") else ""
            lines.append(f"  • id={u['id']:<3} name={u['name']:<20} email={u['email']}{tag}")
        return f"👥 {len(users)} user(s):\n" + "\n".join(lines)

    return "🤔 I didn't understand that. Type 'help' to see commands."


# ---------- MAIN ----------
def main():
    session = Session()
    print("=" * 60)
    print("🤖 PG Chatbot — type 'help' to see commands, 'exit' to quit.")
    print("=" * 60)
    log("SESSION START")

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Bye!")
            log("SESSION END (interrupt)")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            print("👋 Bye!")
            log("SESSION END (exit)")
            break

        if user_input.lower() in ("help", "?"):
            print(HELP_TEXT.strip())
            continue

        if user_input.lower() == "whoami":
            if session.is_logged_in:
                tag = " (admin)" if session.user.get("is_admin") else ""
                print(f"👤 Logged in as {session.user['name']}{tag} (id={session.user_id})")
            else:
                print("👤 Not logged in.")
            continue

        intent = parse_intent(user_input)
        log(f"INPUT | {user_input[:120]}")
        log(f"INTENT | {intent}")

        reply = handle_intent(intent, session)
        print(f"\n🤖 {reply}")


if __name__ == "__main__":
    main()