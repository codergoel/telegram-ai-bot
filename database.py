from pymongo import MongoClient, ASCENDING
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]

# Define collections
users_collection = db["users"]
chats_collection = db["chats"]
files_collection = db["files"]

# Ensure indexes for optimized queries
users_collection.create_index([("chat_id", ASCENDING)], unique=True)
chats_collection.create_index([("chat_id", ASCENDING), ("timestamp", ASCENDING)])
files_collection.create_index([("chat_id", ASCENDING), ("timestamp", ASCENDING)])

def save_user(user_id, first_name, username):
    """
    Save user details in MongoDB efficiently using upsert.
    Ensures a new user is created only if they don’t exist.
    """
    result = users_collection.update_one(
        {"chat_id": user_id},
        {
            "$setOnInsert": {
                "first_name": first_name,
                "username": username,
                "phone_number": None,  # To be updated later
                "created_at": datetime.utcnow()
            }
        },
        upsert=True  # Insert if not exists
    )
    return result.upserted_id is not None  # Returns True if a new user was created

def update_phone_number(user_id, phone_number):
    """
    Update the user's phone number in MongoDB.
    Uses `$set` to only update this field efficiently.
    """
    users_collection.update_one({"chat_id": user_id}, {"$set": {"phone_number": phone_number}})

def save_chat(user_id, user_message, bot_response):
    """
    Store chat history in MongoDB with timestamps.
    """
    chats_collection.insert_one({
        "chat_id": user_id,
        "user_message": user_message,
        "bot_response": bot_response,
        "timestamp": datetime.utcnow()
    })

def save_file_metadata(user_id, file_id, file_name, file_type, description):
    """
    Store file details and analysis in MongoDB.
    Ensures metadata is stored efficiently.
    """
    files_collection.insert_one({
        "chat_id": user_id,
        "file_id": file_id,
        "file_name": file_name,
        "file_type": file_type,
        "description": description,
        "timestamp": datetime.utcnow()
    })
