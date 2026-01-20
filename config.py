import os
from datetime import timedelta
from dotenv import load_dotenv

# -------------------------------------------------
# Load environment variables from .env
# -------------------------------------------------
load_dotenv()


class Config:
    # -------------------------------------------------
    # DATABASE CONFIGURATION
    # -------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:manu262004@localhost:5432/ecopackai"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -------------------------------------------------
    # FLASK CONFIGURATION
    # -------------------------------------------------
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "ecopackai-flask-secret-key-2024"
    )
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    # -------------------------------------------------
    # JWT CONFIGURATION
    # -------------------------------------------------
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY is missing. "
            "Make sure it exists in your .env file."
        )

    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_ALGORITHM = "HS256"
    JWT_DECODE_LEEWAY = 10
