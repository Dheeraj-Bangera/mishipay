import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/usage_db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Optional but recommended to disable tracking modifications for performance

class TestingConfig(Config):
    TESTING = True
    # SQLALCHEMY_DATABASE_URI = "postgresql://user:password@db:5432/test_db"  # Use a separate test database if needed
