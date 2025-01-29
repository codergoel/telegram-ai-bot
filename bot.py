from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import os
from dotenv import load_dotenv
from database import save_user, update_phone_number

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

# Handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.CONTACT, contact_handler))

# Run bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run_polling()
