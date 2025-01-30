import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

def get_gemini_response(user_input):
    """Generate a response using Google's Gemini AI."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")  # ✅ Updated to Gemini 1.5
        response = model.generate_content(user_input)
        return response.text.strip() if response else "I'm sorry, I couldn't process that."
    except Exception as e:
        return f"Error: {str(e)}"

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
