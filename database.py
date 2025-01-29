from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users_collection = db["users"]

def save_user(user_id, first_name, username):
    """Save user details in MongoDB."""
    if not users_collection.find_one({"chat_id": user_id}):
        users_collection.insert_one({
            "chat_id": user_id,
            "first_name": first_name,
            "username": username,
            "phone_number": None  # To be updated later
        })
        return True
    return False

def update_phone_number(user_id, phone_number):
    """Update user’s phone number in MongoDB."""
    users_collection.update_one({"chat_id": user_id}, {"$set": {"phone_number": phone_number}})
