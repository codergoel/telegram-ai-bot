from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import os
from dotenv import load_dotenv
from database import save_user, update_phone_number, save_file_metadata
from gemini_api import get_gemini_response, analyze_image
from database import save_chat
from web_search import perform_web_search


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



# Handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.add_handler(CommandHandler("websearch", handle_websearch))





# Run bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run_polling()
