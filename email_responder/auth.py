import json
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_authenticated_service():
    """
    Authenticate with Gmail API and return service object.
    Returns:
        googleapiclient.discovery.Resource: Authenticated Gmail service object
        None: If authentication fails
    """
    creds = _load_or_refresh_credentials()
    if not creds:
        return None
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail service successfully initialized")
        return service
    except Exception as e:
        print(f"❌ Failed to build Gmail service: {str(e)}")
        return None

def _load_or_refresh_credentials():
    """Handle the complete OAuth flow with error handling."""
    creds = _load_existing_credentials()
    
    if not creds or not creds.valid:
        creds = _refresh_or_authorize(creds)
        if not creds:
            return None
        
        _save_credentials(creds)
    
    return creds

def _load_existing_credentials():
    """Load credentials from token.json if exists."""
    if not os.path.exists('token.json'):
        return None
        
    try:
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        print("🔑 Loaded existing credentials")
        return creds
    except Exception as e:
        print(f"⚠️ Error loading credentials: {str(e)}")
        return None

def _refresh_or_authorize(creds):
    """Refresh expired credentials or initiate new authorization."""
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            print("🔄 Refreshed expired credentials")
            return creds
        except Exception as e:
            print(f"⚠️ Failed to refresh credentials: {str(e)}")
    
    return _authorize_new_credentials()

def _authorize_new_credentials():
    """Perform OAuth 2.0 authorization flow."""
    if not os.path.exists('credentials.json'):
        print("❌ Missing 'credentials.json' file")
        return None
        
    try:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        print("🔐 New authorization completed")
        return creds
    except Exception as e:
        print(f"⚠️ Authorization failed: {str(e)}")
        return None

def _save_credentials(creds):
    """Save credentials to token.json."""
    try:
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
        print("💾 Saved credentials to token.json")
    except Exception as e:
        print(f"⚠️ Failed to save credentials: {str(e)}")

def is_authenticated():
    """Check if valid credentials exist."""
    return os.path.exists('token.json')

# Example usage
if __name__ == "__main__":
    service = get_authenticated_service()
    if service:
        print("Authentication successful!")
    else:
        print("Authentication failed")