import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")  # Populated by Docker Compose
    SQLALCHEMY_TRACK_MODIFICATIONS = False
