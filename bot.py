from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.helpers import escape_markdown
import os
from dotenv import load_dotenv
from database import save_user, update_phone_number, save_file_metadata, save_chat
from gemini_api import get_gemini_response, analyze_image
from web_search import perform_web_search
from pymongo import MongoClient
import random

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users_collection = db["users"]

# Initialize bot application
app = Application.builder().token(BOT_TOKEN).build()

# 🔹 Function to generate follow-up prompts creatively
def generate_follow_up(user_message):
    follow_ups = [
        "Would you like to know more details? 🤔",
        "That’s interesting! Should I provide examples? 📖",
        "Let me know if you need further insights! 😊",
        "Want a fun fact about this topic? 🤩",
        "I can simplify this if you’d like! 🧐"
    ]
    return random.choice(follow_ups)

# 🔹 /start command
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = user.id
    first_name = user.first_name
    username = user.username

    # Save user in MongoDB
    if save_user(chat_id, first_name, username):
        welcome_text = f"""
👋 *Hello {escape_markdown(first_name, version=2)}!*  
🤖 Welcome to *AI Bot*! Here’s what you can do:  
🔹 *Chat with AI* – Send any message and get smart responses  
🖼️ *Analyze Images* – Upload a picture for AI insights  
🌍 *Web Search* – Use `/websearch query` for instant results  
🎁 *Earn Rewards* – Refer friends with `/start {chat_id}`  

📱 *Please share your phone number to continue:*  
(Use the button below ⬇️)
"""
        await update.message.reply_text(
            welcome_text, parse_mode="MarkdownV2",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📱 Share Phone Number", request_contact=True)]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
    else:
        await update.message.reply_text("🔹 *Welcome back\\!* You are already registered\\. 😊", parse_mode="MarkdownV2")


# 🔹 Contact handler
async def contact_handler(update: Update, context: CallbackContext):
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        chat_id = update.message.chat_id
        update_phone_number(chat_id, phone_number)

        await update.message.reply_text("✅ *Phone number saved successfully!* 🎉", parse_mode="MarkdownV2")
    else:
        await update.message.reply_text("❌ *Please use the button to share your phone number.*", parse_mode="MarkdownV2")

# 🔹 AI Chat Handler (Now includes emojis & follow-ups)
async def ai_chat(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user_message = update.message.text

    bot_response = get_gemini_response(user_message)
    formatted_response = escape_markdown(bot_response, version=2)

    # Save chat history
    save_chat(user_id, user_message, bot_response)

    # Generate follow-up question
    follow_up = escape_markdown(generate_follow_up(user_message), version=2)

    await update.message.reply_text(f"💡 *AI Response:*\n{formatted_response}", parse_mode="MarkdownV2")
    await update.message.reply_text(f"🔍 {follow_up}", parse_mode="MarkdownV2")

# 🔹 Handle document uploads
async def handle_document(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    document = update.message.document
    file = await context.bot.get_file(document.file_id)
    file_path = f"downloads/{document.file_name}"

    os.makedirs("downloads", exist_ok=True)
    await file.download_to_drive(file_path)

    description = analyze_image(file_path) if document.mime_type.startswith("image/") else "📄 File received. No analysis available."
    save_file_metadata(user_id, document.file_id, document.file_name, document.mime_type, description)

    formatted_description = escape_markdown(description, version=2)
    await update.message.reply_text(f"📂 *File Received:*\n{formatted_description}", parse_mode="MarkdownV2")

# 🔹 Handle images
async def handle_photo(update: Update, context: CallbackContext):
    try:
        user_id = update.message.chat_id
        photo = update.message.photo[-1]  
        file = await context.bot.get_file(photo.file_id)
        file_path = f"downloads/{photo.file_id}.jpg"

        os.makedirs("downloads", exist_ok=True)
        await file.download_to_drive(file_path)

        description = analyze_image(file_path)
        save_file_metadata(user_id, photo.file_id, f"{photo.file_id}.jpg", "image", description)

        formatted_description = escape_markdown(description, version=2)

        for chunk in [formatted_description[i:i+4000] for i in range(0, len(formatted_description), 4000)]:
            await update.message.reply_text(chunk, parse_mode="MarkdownV2")

    except Exception as e:
        await update.message.reply_text(f"❌ *Error processing image:* `{escape_markdown(str(e), version=2)}`", parse_mode="MarkdownV2")

# 🔹 Web Search Handler
async def handle_websearch(update: Update, context: CallbackContext):
    try:
        query = " ".join(context.args)
        if not query:
            await update.message.reply_text("❌ *Please provide a search query.* Example: `/websearch AI news`", parse_mode="MarkdownV2")
            return

        await update.message.reply_text("🔍 *Searching... Please wait.*", parse_mode="MarkdownV2")
        
        summary = perform_web_search(query)
        formatted_summary = escape_markdown(summary, version=2)

        for chunk in [formatted_summary[i:i+4000] for i in range(0, len(formatted_summary), 4000)]:
            await update.message.reply_text(chunk, parse_mode="MarkdownV2")

    except Exception as e:
        await update.message.reply_text(f"❌ *Error processing search:* `{escape_markdown(str(e), version=2)}`", parse_mode="MarkdownV2")

# 🔹 Referral Tracking
async def my_referrals(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user = users_collection.find_one({"chat_id": user_id})

    if not user:
        await update.message.reply_text("❌ *You're not registered yet.*", parse_mode="MarkdownV2")
        return

    referred_by = user.get("referred_by", "None")
    referral_count = user.get("referral_count", 0)

    message = f"🎁 *Referral Stats*\n\n🔹 *Your Referral Code:* `{user_id}`\n🔹 *Referred By:* {referred_by}\n🔹 *People Referred:* {referral_count}"
    await update.message.reply_text(message, parse_mode="MarkdownV2")

# 🔹 Handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.add_handler(CommandHandler("websearch", handle_websearch))
app.add_handler(CommandHandler("myreferrals", my_referrals))

# 🔹 Run bot
if __name__ == "__main__":
    print("🚀 Bot is running...")
    app.run_polling()
