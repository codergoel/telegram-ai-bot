from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import os
from dotenv import load_dotenv
from database import save_user, update_phone_number, save_file_metadata
from gemini_api import get_gemini_response, analyze_image
from database import save_chat
from web_search import perform_web_search
from pymongo import MongoClient

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users_collection = db["users"]

# Load API Token
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize bot application
app = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: CallbackContext):
    """Handles /start command and registers users."""
    user = update.effective_user
    chat_id = user.id
    first_name = user.first_name
    username = user.username

    # Save user in MongoDB
    if save_user(chat_id, first_name, username):
        await update.message.reply_text(
            f"Hello {first_name}! Welcome to the AI Bot. Please share your phone number.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📱 Share Phone Number", request_contact=True)]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
    else:
        await update.message.reply_text("Welcome back! You are already registered.")

async def contact_handler(update: Update, context: CallbackContext):
    """Handles the phone number input from the user."""
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        chat_id = update.message.chat_id
        update_phone_number(chat_id, phone_number)

        await update.message.reply_text("✅ Phone number saved successfully!")
    else:
        await update.message.reply_text("❌ Please use the button to share your phone number.")

async def ai_chat(update: Update, context: CallbackContext):
    """Handles user messages and responds with Gemini AI."""
    user_id = update.message.chat_id
    user_message = update.message.text

    bot_response = get_gemini_response(user_message)

    # Save chat history
    save_chat(user_id, user_message, bot_response)

    await update.message.reply_text(bot_response)


async def handle_document(update: Update, context: CallbackContext):
    """Handles file uploads (PDF, PNG, JPG, etc.)."""
    user_id = update.message.chat_id
    document = update.message.document
    file = await context.bot.get_file(document.file_id)
    file_path = f"downloads/{document.file_name}"

    # Save file locally
    os.makedirs("downloads", exist_ok=True)
    await file.download_to_drive(file_path)

    # Analyze file (only for images)
    if document.mime_type.startswith("image/"):
        description = analyze_image(file_path)
    else:
        description = "📄 File received. No analysis available."

    # Store metadata in MongoDB
    save_file_metadata(user_id, document.file_id, document.file_name, document.mime_type, description)

    await update.message.reply_text(f"📂 File Received:\n{description}")


async def handle_photo(update: Update, context: CallbackContext):
    """Handles images uploaded by the user."""
    try:
        user_id = update.message.chat_id
        photo = update.message.photo[-1]  # Get the highest quality photo
        file = await context.bot.get_file(photo.file_id)
        file_path = f"downloads/{photo.file_id}.jpg"

        # Save image locally
        os.makedirs("downloads", exist_ok=True)
        await file.download_to_drive(file_path)

        # Analyze image
        description = analyze_image(file_path)

        # Store metadata in MongoDB
        save_file_metadata(user_id, photo.file_id, f"{photo.file_id}.jpg", "image", description)

        # Send response in chunks if too long
        for chunk in [description[i:i+4000] for i in range(0, len(description), 4000)]:
            await update.message.reply_text(chunk)

    except Exception as e:
        await update.message.reply_text(f"❌ Error processing image: {str(e)}")

async def handle_websearch(update: Update, context: CallbackContext):
    """Handles the /websearch command."""
    try:
        query = " ".join(context.args)
        if not query:
            await update.message.reply_text("❌ Please provide a search query. Example: `/websearch AI news`")
            return

        await update.message.reply_text("🔍 Searching... Please wait.")
        
        # Perform web search and summarize
        summary = perform_web_search(query)

        # Send response (split if too long)
        for chunk in [summary[i:i+4000] for i in range(0, len(summary), 4000)]:
            await update.message.reply_text(chunk)
    
    except Exception as e:
        await update.message.reply_text(f"❌ Error processing search: {str(e)}")

async def handle_start(update: Update, context: CallbackContext):
    """Handles /start command with referral tracking."""
    user_id = update.message.chat_id
    first_name = update.message.chat.first_name
    username = update.message.chat.username

    # Check if a referral code is provided
    args = context.args
    referred_by = args[0] if args else None

    # Check if user already exists
    user = users_collection.find_one({"chat_id": user_id})
    if user:
        await update.message.reply_text(f"👋 Welcome back, {first_name}!")
        return

    # New user - Save to MongoDB
    new_user = {
        "chat_id": user_id,
        "first_name": first_name,
        "username": username,
        "referral_code": str(user_id),
        "referred_by": referred_by,
        "referral_count": 0
    }
    users_collection.insert_one(new_user)

    # If referred, update referrer's referral count
    if referred_by:
        users_collection.update_one(
            {"chat_id": int(referred_by)},
            {"$inc": {"referral_count": 1}}
        )
        await update.message.reply_text(f"🎉 You joined via referral! Your referrer: {referred_by}")

    await update.message.reply_text(f"👋 Welcome, {first_name}!\n🎁 Your referral code: `{user_id}`\nRefer others using `/start {user_id}` to earn rewards!")

async def my_referrals(update: Update, context: CallbackContext):
    """Handles /myreferrals command to check referrals."""
    user_id = update.message.chat_id
    user = users_collection.find_one({"chat_id": user_id})

    if not user:
        await update.message.reply_text("❌ You're not registered yet.")
        return

    referred_by = user.get("referred_by", "None")
    referral_count = user.get("referral_count", 0)

    message = f"🎁 **Referral Stats**\n\n🔹 Your Referral Code: `{user_id}`\n🔹 Referred By: {referred_by}\n🔹 People Referred: {referral_count}"
    await update.message.reply_text(message)


# Handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.add_handler(CommandHandler("websearch", handle_websearch))
app.add_handler(CommandHandler("start", handle_start))
app.add_handler(CommandHandler("myreferrals", my_referrals))

# Run bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run_polling()
