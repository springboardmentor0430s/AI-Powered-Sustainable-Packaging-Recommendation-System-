import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-very-secret'
    # Default to SQLite for ease of use, but allow Postgres override
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ecopack.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
