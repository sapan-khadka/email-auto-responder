import os
import base64
import logging

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from email_responder.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Required Gmail API scopes
SCOPES = [
    'https://mail.google.com/',  # Full access
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels'
]

def get_gmail_service():
    """Authenticate with Gmail API and return service object."""
    creds = None

    # Load existing token
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            os.remove('token.json')
            return get_gmail_service()

    # Start new OAuth flow if needed
    if not creds or not creds.valid:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(Config.CREDS_FILE, SCOPES)
            creds = flow.run_local_server(
                port=0,
                authorization_prompt_message='Please authorize access to your Gmail account',
                success_message='✅ Authentication complete! You may close this window.',
                open_browser=True
            )

            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    try:
        return build('gmail', 'v1', credentials=creds)
    except Exception as e:
        logger.error(f"Failed to build Gmail service: {e}")
        raise

def send_email(service, to, subject, message_text, thread_id=None):
    """Send an email, optionally replying in a thread."""
    try:
        message = (
            f"To: {to}\n"
            f"Subject: {subject}\n\n"
            f"{message_text}"
        )

        encoded_message = base64.urlsafe_b64encode(
            message.encode("utf-8")
        ).decode("utf-8")

        send_body = {
            'raw': encoded_message
        }

        if thread_id:
            send_body['threadId'] = thread_id

        sent = service.users().messages().send(userId='me', body=send_body).execute()
        logger.info(f"✅ Email sent to {to} | ID: {sent['id']}")
        return True

    except HttpError as error:
        if error.resp.status == 403:
            logger.error("❌ Insufficient permissions. Removing token to reset authentication...")
            if os.path.exists('token.json'):
                os.remove('token.json')
        logger.error(f"❌ Gmail API error: {error}")
        return False

    except Exception as e:
        logger.error(f"❌ Unexpected error while sending email: {e}")
        return False
