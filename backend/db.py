import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

# Load .env explicitly
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

print("🔐 DB_HOST =", os.getenv("DB_HOST"))
print("🔐 DB_USER =", os.getenv("DB_USER"))
print("🔐 DB_PASSWORD =", os.getenv("DB_PASSWORD"))

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        return conn
    except Exception as e:
        print("❌ DB CONNECTION ERROR:", e)
        raise  # 🔥 THIS IS CRITICAL

