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
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(user_input)
        return response.text.strip() if response else "I'm sorry, I couldn't process that."
    except Exception as e:
        return f"Error: {str(e)}"
