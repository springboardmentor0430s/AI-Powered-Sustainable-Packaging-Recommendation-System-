class Config:
    # Flask secret key
    SECRET_KEY = "super-secret-key"

    # PostgreSQL connection (EDIT PASSWORD ONLY)
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:anits@localhost:5432/ecopackai"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT secret key
    JWT_SECRET_KEY = "jwt-secret-key"
