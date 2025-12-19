import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load biến môi trường
env_path = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
load_dotenv(dotenv_path=env_path)

# Kết nối MongoDB
MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("MONGODB_DATABASE")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
