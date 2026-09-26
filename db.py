import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Create and return a new PostgreSQL connection."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode="require",
    )


def init_db():
    """Create the users table if it doesn't exist (with is_admin)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            SERIAL PRIMARY KEY,
            name          VARCHAR(100) NOT NULL,
            address       TEXT NOT NULL,
            cnic          VARCHAR(15) UNIQUE NOT NULL,
            email         VARCHAR(150) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin      BOOLEAN NOT NULL DEFAULT FALSE,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # Safe migration for existing tables:
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;")
    conn.commit()
    cur.close()
    conn.close()
    print("✅ users table ready")


if __name__ == "__main__":
    init_db()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_name = 'users' ORDER BY ordinal_position;")
    print("\n📋 Table structure:")
    for row in cur.fetchall():
        print(f"  {row[0]:<15} {row[1]}")
    cur.close()
    conn.close()