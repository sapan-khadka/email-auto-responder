import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration settings for the Smart Email Auto-Responder.
    """
    
    # Gmail API Credentials
    CREDS_FILE = os.getenv("CREDS_FILE", "credentials.json")

    # Gmail API Scopes
    SCOPES = [
        'https://mail.google.com/',  # Full access
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.labels'
    ]

    # Time interval (in seconds) to check for new emails in auto mode
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 60))
