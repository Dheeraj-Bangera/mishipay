import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/usage_db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False 


    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = os.getenv("REDIS_PORT", 6379)
    REDIS_DB = os.getenv("REDIS_DB", 0)

class TestingConfig(Config):
    TESTING = True
    REDIS_URL = 'redis://localhost:6379/0'
