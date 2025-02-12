import os
from dotenv import load_dotenv

load_dotenv()

# settings for flask app

class Config:
    SECRET_KEY = os.urandom(24) # secure sessions and cookies by randomly generating 24 bytes
    SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False # not track crud opeartions modifications 
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
