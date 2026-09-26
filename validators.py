import re

# ---------- INDIVIDUAL VALIDATORS ----------

def validate_name(name: str) -> tuple[bool, str]:
    """Only letters and spaces, 2-100 chars."""
    if not name or not name.strip():
        return False, "Name cannot be empty."
    if not re.fullmatch(r"[A-Za-z ]{2,100}", name.strip()):
        return False, "Name must be 2-100 letters/spaces only."
    return True, name.strip()


def validate_address(address: str) -> tuple[bool, str]:
    """Non-empty, 5-255 chars."""
    if not address or not address.strip():
        return False, "Address cannot be empty."
    if len(address.strip()) < 5:
        return False, "Address is too short (min 5 chars)."
    if len(address.strip()) > 255:
        return False, "Address is too long (max 255 chars)."
    return True, address.strip()


def validate_cnic(cnic: str) -> tuple[bool, str]:
    """Format: 12345-6789012-3 (13 digits with dashes)."""
    if not cnic:
        return False, "CNIC cannot be empty."
    cnic = cnic.strip()
    if not re.fullmatch(r"\d{5}-\d{7}-\d", cnic):
        return False, "CNIC must be in format 12345-6789012-3."
    return True, cnic


def validate_email(email: str) -> tuple[bool, str]:
    """Basic email pattern check."""
    if not email:
        return False, "Email cannot be empty."
    email = email.strip().lower()
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.fullmatch(pattern, email):
        return False, "Invalid email format."
    return True, email


def validate_password(password: str) -> tuple[bool, str]:
    """Min 8 chars, at least 1 letter and 1 digit."""
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    return True, password


# ---------- FULL FORM VALIDATOR ----------

def validate_form(data: dict) -> tuple[bool, dict, list[str]]:
    """
    Validate a full registration form.
    Returns (is_valid, cleaned_data, errors).
    """
    errors = []
    cleaned = {}

    for field, validator in [
        ("name", validate_name),
        ("address", validate_address),
        ("cnic", validate_cnic),
        ("email", validate_email),
        ("password", validate_password),
    ]:
        ok, result = validator(data.get(field, ""))
        if ok:
            cleaned[field] = result
        else:
            errors.append(f"{field}: {result}")

    return (len(errors) == 0, cleaned, errors)


# ---------- QUICK TEST ----------

if __name__ == "__main__":
    sample = {
        "name": "Ali Khan",
        "address": "House 12, Street 5, Lahore",
        "cnic": "35202-1234567-1",
        "email": "ali@example.com",
        "password": "secret123",
    }

    ok, cleaned, errs = validate_form(sample)
    print("Valid:", ok)
    print("Cleaned:", cleaned)
    print("Errors:", errs)

    print("\n--- Invalid case ---")
    bad = {
        "name": "Ali123",
        "address": "x",
        "cnic": "123",
        "email": "not-an-email",
        "password": "abc",
    }
    ok, cleaned, errs = validate_form(bad)
    print("Valid:", ok)
    print("Errors:")
    for e in errs:
        print(" -", e)