import google.generativeai as genai
import os
from dotenv import load_dotenv
import random

# Load API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

def get_gemini_response(user_input):
    """Generate a response using Google's Gemini AI with context and follow-ups."""
    try:
        # Define system prompt to guide Gemini's behavior
        system_prompt = """
You are an AI chatbot assistant for a Telegram bot.  
Your job is to provide helpful, concise, and engaging responses.  
Make responses interactive, use emojis where appropriate, and ensure clear formatting.  
Keep answers short unless a detailed explanation is required.  
After each response, suggest a relevant follow-up question to continue engagement.  
"""

        # Combine system instructions with user query
        final_prompt = f"{system_prompt}\nUser: {user_input}\nBot:"

        # Generate response using Gemini API
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(final_prompt)

        if not response or not response.text:
            return "I'm sorry, I couldn't process that. ❌"

        # Add a follow-up prompt for user engagement
        follow_ups = [
            "Would you like more details on this? 🤔",
            "Need a related example? 😊",
            "Do you want a step-by-step guide? 🚀",
            "Let me know if you have any other questions! ✨"
        ]
        follow_up = random.choice(follow_ups)

        return f"{response.text.strip()}\n\n{follow_up}"

    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def analyze_image(file_path, prompt="Describe this image."):
    """Analyze an image using Google's Gemini 1.5 model."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")  # ✅ Updated to Gemini 1.5

        # Read image in binary mode
        with open(file_path, "rb") as image_file:
            image_data = image_file.read()

        # ✅ Gemini 1.5 requires both image + text
        response = model.generate_content([
            {"mime_type": "image/jpeg", "data": image_data},  # Image
            prompt  # Text prompt
        ])

        # Extract text description
        description = response.text.strip() if response else "No description available."

        # Ensure it does not exceed Telegram's character limit
        if len(description) > 4000:
            description = description[:4000] + "..."  # Truncate long responses

        return description
    except Exception as e:
        return f"Error: {str(e)}"
