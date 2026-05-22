import os
from dotenv import load_dotenv

# Load local environment variables from a .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-cosmic-secret-key-1982')
    
    # Database Configuration - Defaults to local sqlite if Postgres URL isn't set yet
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///celestial.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- MONETIZATION CONFIGURATION ---
    # Set to True during early access launch. Everyone gets premium features for free.
    # Set to False in production when you are ready to enforce Stripe paywalls.
    GLOBAL_FREE_BETA = os.environ.get('GLOBAL_FREE_BETA', 'True').lower() in ['true', '1', 'yes']