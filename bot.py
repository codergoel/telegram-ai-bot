from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import os
from dotenv import load_dotenv
from database import save_user, update_phone_number
from gemini_api import get_gemini_response
from database import save_chat


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


# Handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat))


# Run bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run_polling()
