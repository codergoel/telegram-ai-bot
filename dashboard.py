from flask import Flask, render_template
from pymongo import MongoClient
import os

app = Flask(__name__)

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users_collection = db["users"]
chats_collection = db["chats"]

@app.route("/")
def dashboard():
    total_users = users_collection.count_documents({})
    active_users = users_collection.count_documents({"last_active": {"$exists": True}})
    total_messages = chats_collection.count_documents({})
    top_users = list(users_collection.find().sort("referral_count", -1).limit(5))

    return render_template("dashboard.html", total_users=total_users, active_users=active_users, total_messages=total_messages, top_users=top_users)

if __name__ == "__main__":
    app.run(debug=True)
