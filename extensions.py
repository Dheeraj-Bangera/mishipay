from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from config import Config


db = SQLAlchemy()


redis_client = Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB)
