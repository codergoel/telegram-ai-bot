import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# Load API Keys
load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")  # Use SerpAPI or another search API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

def perform_web_search(query):
    """Fetch top search results using SerpAPI and summarize using Gemini."""
    try:
        search_url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 5  # Limit to top 5 results
        }
        response = requests.get(search_url, params=params)
        results = response.json().get("organic_results", [])

        if not results:
            return "No search results found."

        # Extract relevant data
        search_data = "\n".join([f"{i+1}. {res['title']}: {res['link']}" for i, res in enumerate(results)])

        # Use Gemini to summarize results
        model = genai.GenerativeModel("gemini-1.5-flash")
        summary_prompt = f"Summarize the following search results:\n{search_data}"
        summary = model.generate_content(summary_prompt).text.strip()

        return f"🔎 **AI-Powered Web Search Summary:**\n{summary}\n\n🌐 **Top Links:**\n{search_data}"
    
    except Exception as e:
        return f"❌ Error in web search: {str(e)}"
