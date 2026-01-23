import psycopg2
import psycopg2.errors
from psycopg2.extras import RealDictCursor
import hashlib
import os

def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            port=os.environ.get("DB_PORT", 5432)
        )
    except Exception as e:
        print(f"⚠️ DB unavailable: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if not conn:
        print("⚠️ Skipping DB init")
        return

    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                product_category VARCHAR(100),
                weight_g FLOAT,
                fragility_level FLOAT,
                dimensions_cm FLOAT,
                strength FLOAT,
                predicted_cost FLOAT,
                predicted_co2 FLOAT,
                recommended_material VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        print("✅ DB tables created/verified")
    except Exception as e:
        conn.rollback()
        print(f"❌ DB init error: {e}")
    finally:
        cur.close()
        conn.close()

def create_user(username, email, password):
    conn = get_db_connection()
    if not conn:
        return False

    cur = conn.cursor()
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cur.execute("""
            INSERT INTO users (username, email, password)
            VALUES (%s, %s, %s)
        """, (username, email, password_hash))
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def authenticate_user(username_or_email, password):
    conn = get_db_connection()
    if not conn:
        return None

    cur = conn.cursor(cursor_factory=RealDictCursor)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cur.execute("""
        SELECT id, username
        FROM users
        WHERE (username = %s OR email = %s)
        AND password = %s
    """, (username_or_email, username_or_email, password_hash))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user
if os.environ.get("AUTO_INIT_DB") == "true":
    init_db()