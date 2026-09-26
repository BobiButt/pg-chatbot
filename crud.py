from db import get_connection
from security import hash_password, verify_password


# ---------- CREATE ----------

def create_user(name: str, address: str, cnic: str, email: str, password: str,
                is_admin: bool = False) -> dict:
    conn = get_connection()
    try:
        cur = conn.cursor()
        password_hash = hash_password(password)
        cur.execute(
            """
            INSERT INTO users (name, address, cnic, email, password_hash, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, name, address, cnic, email, is_admin, created_at
            """,
            (name, address, cnic, email, password_hash, is_admin),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        return {
            "id": row[0], "name": row[1], "address": row[2],
            "cnic": row[3], "email": row[4], "is_admin": row[5],
            "created_at": row[6],
        }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()


# ---------- READ ----------

def get_user_by_id(user_id: int) -> dict | None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, address, cnic, email, is_admin, created_at "
            "FROM users WHERE id = %s",
            (user_id,),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            return None
        return {
            "id": row[0], "name": row[1], "address": row[2],
            "cnic": row[3], "email": row[4], "is_admin": row[5],
            "created_at": row[6],
        }
    finally:
        conn.close()


def get_user_by_email(email: str) -> dict | None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, address, cnic, email, password_hash, is_admin, created_at "
            "FROM users WHERE email = %s",
            (email,),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            return None
        return {
            "id": row[0], "name": row[1], "address": row[2],
            "cnic": row[3], "email": row[4], "password_hash": row[5],
            "is_admin": row[6], "created_at": row[7],
        }
    finally:
        conn.close()


def get_user_by_cnic(cnic: str) -> dict | None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, address, cnic, email, is_admin, created_at "
            "FROM users WHERE cnic = %s",
            (cnic,),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            return None
        return {
            "id": row[0], "name": row[1], "address": row[2],
            "cnic": row[3], "email": row[4], "is_admin": row[5],
            "created_at": row[6],
        }
    finally:
        conn.close()


def list_users() -> list[dict]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, cnic, is_admin FROM users ORDER BY id")
        rows = cur.fetchall()
        cur.close()
        return [
            {"id": r[0], "name": r[1], "email": r[2], "cnic": r[3], "is_admin": r[4]}
            for r in rows
        ]
    finally:
        conn.close()


# ---------- UPDATE ----------

def update_user_field(user_id: int, field: str, value) -> dict:
    allowed = {"name", "address", "cnic", "email", "password_hash", "is_admin"}
    if field not in allowed:
        return {"error": f"Field '{field}' not allowed."}

    if field == "password_hash":
        value = hash_password(value)

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE users SET {field} = %s WHERE id = %s "
            f"RETURNING id, name, address, cnic, email, is_admin, created_at",
            (value, user_id),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        if not row:
            return {"error": "User not found."}
        return {
            "id": row[0], "name": row[1], "address": row[2],
            "cnic": row[3], "email": row[4], "is_admin": row[5],
            "created_at": row[6],
        }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()


# ---------- DELETE ----------

def delete_user(user_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        return deleted
    finally:
        conn.close()


def delete_user_by_email(email: str) -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE email = %s", (email,))
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        return deleted
    finally:
        conn.close()


# ---------- AUTH ----------

def authenticate(email: str, password: str) -> dict | None:
    user = get_user_by_email(email)
    if not user:
        return None
    if verify_password(password, user["password_hash"]):
        user.pop("password_hash")
        return user
    return None


# ---------- QUICK TEST ----------

if __name__ == "__main__":
    print("--- CREATE ---")
    u = create_user(
        name="Test User",
        address="123 Test Street, Lahore",
        cnic="35202-9999999-1",
        email="test@example.com",
        password="testpass123",
    )
    print(u)

    if "error" not in u:
        print("\n--- READ by id ---");       print(get_user_by_id(u["id"]))
        print("\n--- READ by email ---");    print(get_user_by_email("test@example.com"))
        print("\n--- UPDATE address ---");   print(update_user_field(u["id"], "address", "New Address"))
        print("\n--- AUTH (correct) ---");   print(authenticate("test@example.com", "testpass123"))
        print("\n--- AUTH (wrong) ---");     print(authenticate("test@example.com", "wrong"))
        print("\n--- DELETE ---");           print("Deleted:", delete_user(u["id"]))

    print("\n--- LIST ALL ---")
    for row in list_users():
        print(row)