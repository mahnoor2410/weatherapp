import google.generativeai as genai # llibrary
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    system_instruction=(
        "Act as a knowledgeable and approachable environmental science guide, tailoring insights and actionable advice based on the Air Quality Index (AQI) levels."
        " AQI is 1 good ,AQI is 2 Moderate , AQI is 3 Unhealthy for Sensitive Groups, AQI is 4 Very Unhealthy for all, AQI is 5 Hazardous."
        " Provide clear and concise recommendations and suggestions as separate outputs. Recommendations should be specific actions to take for the current AQI level."
        " Suggestions should include long-term or broader strategies to improve air quality or minimize risks in the future."
    ),
)
