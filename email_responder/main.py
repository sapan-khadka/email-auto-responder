import os
import time
import re
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email_responder.utils.email_utils import send_email
from email_responder.utils.nlp_utils import preprocess_text
from email_responder.models.classifier import EmailClassifier
from email_responder.models.response_generator import ResponseGenerator
from email_responder.config import Config

# Gmail API Scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

def authenticate():
    """Authenticate with Gmail and return the service."""
    creds = None

    # Check if 'token.json' exists and load credentials
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            print("✅ Loaded credentials from token.json")
        except Exception as e:
            print(f"⚠️ Error loading credentials: {e}")
            creds = None

    # If no valid credentials, authenticate using OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("🔄 Refreshed expired credentials.")
            except Exception as e:
                print(f"⚠️ Error refreshing credentials: {e}")
                creds = None

        if not creds:
            try:
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError("Missing 'credentials.json' file for OAuth 2.0")

                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                print("🔑 New credentials obtained.")
            except Exception as e:
                print(f"⚠️ Authentication failed: {e}")
                return None

        # Save the credentials
        try:
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            print("💾 Saved credentials to token.json")
        except Exception as e:
            print(f"⚠️ Error saving credentials: {e}")

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"⚠️ Failed to build Gmail service: {e}")
        return None

def fetch_emails(service, limit=5):
    """Fetch unread emails and return structured data."""
    try:
        results = service.users().messages().list(
            userId='me',
            labelIds=['INBOX', 'UNREAD'],
            maxResults=limit
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            return []

        email_data = []
        for msg in messages:
            try:
                email = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()

                headers = {h['name']: h['value'] for h in email['payload']['headers']}
                sender = headers.get('From', 'Unknown')
                subject = headers.get('Subject', '(No Subject)')
                snippet = email.get('snippet', '')
                thread_id = email.get('threadId', '')
                
                # Get full message body if available
                body = get_email_body(email['payload'])

                email_data.append({
                    'id': msg['id'],
                    'from': sender,
                    'subject': subject,
                    'snippet': snippet,
                    'body': body,
                    'threadId': thread_id
                })
            except Exception as e:
                print(f"⚠️ Error processing email {msg['id']}: {e}")
                continue

        return email_data
    except Exception as e:
        print(f"⚠️ Error fetching emails: {e}")
        return []

def get_email_body(payload):
    """Extract email body from payload."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                return part['body'].get('data', '')
    return payload.get('body', {}).get('data', '')

def process_emails(service, classifier, responder):
    """Process unread emails, classify, and auto-respond."""
    try:
        emails = fetch_emails(service)
        if not emails:
            print("📭 No new emails found.")
            return

        for email in emails:
            try:
                processed_text = preprocess_text(email['body'])
                label = classifier.predict(processed_text)

                if label.lower() != "spam":
                    response = responder.generate_response(email['body'])
                    sender_email = extract_email(email['from'])
                    
                    send_email_reply(
                        service,
                        to=sender_email,
                        subject=f"Re: {email['subject']}",
                        message=response,
                        thread_id=email['threadId']
                    )
                    print(f"✅ Replied to: {sender_email} | Subject: {email['subject']}")
                else:
                    print(f"❌ Skipped spam from {email['from']}")

                # Mark as read
                service.users().messages().modify(
                    userId='me',
                    id=email['id'],
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
            except Exception as e:
                print(f"⚠️ Error processing email from {email.get('from', 'unknown')}: {e}")
                continue
    except Exception as e:
        print(f"⚠️ Error in email processing: {e}")

def send_email_reply(service, to, subject, message, thread_id=None):
    """Send a reply email."""
    try:
        send_email(
            service=service,
            to=to,
            subject=subject,
            message_text=message,
            thread_id=thread_id
        )
    except Exception as e:
        print(f"⚠️ Failed to send email reply: {e}")

def extract_email(sender_str):
    """Extract plain email from sender string."""
    match = re.search(r'<(.+?)>', sender_str)
    return match.group(1) if match else sender_str

def main():
    """Run the email auto-responder."""
    print("🚀 Starting email auto-responder...")
    
    # Initialize components
    service = authenticate()
    if not service:
        print("❌ Failed to initialize Gmail service. Exiting.")
        return

    classifier = EmailClassifier()
    responder = ResponseGenerator()

    # Train classifier with sample data (in a real app, load from dataset)
    classifier.train(
        texts=["urgent meeting tomorrow", "hi friend how are you", 
               "free money click here", "project status update"],
        labels=["urgent", "personal", "spam", "general"]
    )

    try:
        print(f"⏳ Checking emails every {Config.CHECK_INTERVAL} seconds...")
        while True:
            process_emails(service, classifier, responder)
            time.sleep(Config.CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n🛑 Stopping auto-responder...")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")

if __name__ == "__main__":
    main()