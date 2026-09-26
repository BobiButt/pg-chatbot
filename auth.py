from security import verify_password
from crud import create_user, authenticate
from validators import validate_form


# ---------- SESSION ----------

class Session:
    """Holds the currently logged-in user for the chatbot."""
    def __init__(self):
        self.user = None  # dict or None

    def login(self, user: dict):
        self.user = user

    def logout(self):
        self.user = None

    @property
    def is_logged_in(self) -> bool:
        return self.user is not None

    @property
    def user_id(self) -> int | None:
        return self.user["id"] if self.user else None


# ---------- REGISTER / LOGIN ----------

def register(session: Session, name: str, address: str, cnic: str, email: str, password: str) -> tuple[bool, str]:
    ok, cleaned, errors = validate_form({
        "name": name,
        "address": address,
        "cnic": cnic,
        "email": email,
        "password": password,
    })
    if not ok:
        return False, "Validation failed:\n  - " + "\n  - ".join(errors)

    result = create_user(
        name=cleaned["name"],
        address=cleaned["address"],
        cnic=cleaned["cnic"],
        email=cleaned["email"],
        password=cleaned["password"],
    )

    if "error" in result:
        err = result["error"].lower()
        if "users_email_key" in err:
            return False, "Email already registered."
        if "users_cnic_key" in err:
            return False, "CNIC already registered."
        return False, f"DB error: {result['error']}"

    session.login(result)
    return True, f"✅ Registered & logged in as {result['name']} (id={result['id']})."


def login(session: Session, email: str, password: str) -> tuple[bool, str]:
    user = authenticate(email.strip().lower(), password)
    if not user:
        return False, "❌ Invalid email or password."
    session.login(user)
    return True, f"✅ Welcome back, {user['name']}!"


def logout(session: Session) -> tuple[bool, str]:
    if not session.is_logged_in:
        return False, "You are not logged in."
    name = session.user["name"]
    session.logout()
    return True, f"👋 Goodbye, {name}. You have been logged out."


# ---------- QUICK TEST ----------

if __name__ == "__main__":
    s = Session()

    print("--- REGISTER (valid) ---")
    print(register(s, "Ali Khan", "House 5, Lahore", "35202-1111111-1", "ali@test.com", "pass1234"))
    print("Logged in as:", s.user)

    print("\n--- REGISTER (duplicate email) ---")
    print(register(s, "Other Guy", "Somewhere, Karachi", "35202-2222222-2", "ali@test.com", "pass1234"))

    print("\n--- REGISTER (invalid input) ---")
    print(register(s, "X", "y", "123", "bad", "abc"))

    print("\n--- LOGOUT ---")
    print(logout(s))
    print("Logged in?", s.is_logged_in)

    print("\n--- LOGIN (correct) ---")
    print(login(s, "ali@test.com", "pass1234"))
    print("User id:", s.user_id)

    print("\n--- LOGIN (wrong password) ---")
    s.logout()
    print(login(s, "ali@test.com", "wrong"))

    # Cleanup
    from crud import delete_user, get_user_by_email
    u = get_user_by_email("ali@test.com")
    if u:
        delete_user(u["id"])
        print("\n🧹 Cleaned up test user.")