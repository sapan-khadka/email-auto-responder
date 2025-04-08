import streamlit as st
from email_responder.models.response_generator import ResponseGenerator
from email_responder import main as responder_main
from email_responder.models.classifier import EmailClassifier
import asyncio

# Initialize event loop for async operations
asyncio.set_event_loop(asyncio.new_event_loop())

# ------------------------------
# Streamlit App Config
# ------------------------------
st.set_page_config(page_title="📧 SmartReply AI", layout="wide")
st.title("📬 SmartReply AI - Smart Email Auto-Responder")

# Initialize session state variables
if 'gmail_service' not in st.session_state:
    st.session_state.gmail_service = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# ------------------------------
# Initialize Components
# ------------------------------
response_generator = ResponseGenerator()
classifier = EmailClassifier()  # Initialize once to avoid reloading

# ------------------------------
# Gmail Authentication Section
# ------------------------------
with st.expander("🔐 Gmail Authentication", expanded=True):
    if st.button("Login via Gmail"):
        try:
            with st.spinner("Authenticating with Gmail..."):
                service = responder_main.authenticate()
                if service:
                    st.session_state.gmail_service = service
                    st.session_state.authenticated = True
                    st.success("✅ Successfully authenticated with Gmail.")
                else:
                    st.error("❌ Failed to authenticate with Gmail.")
        except Exception as e:
            st.error(f"❌ Authentication failed: {str(e)}")

# ------------------------------
# Inbox + Classification Section
# ------------------------------
with st.expander("📥 Inbox & Classification", expanded=True):
    if st.button("Fetch Emails"):
        if not st.session_state.authenticated:
            st.warning("⚠️ Please authenticate with Gmail first.")
            st.stop()

        try:
            with st.spinner("Fetching emails..."):
                emails = responder_main.fetch_emails(
                    st.session_state.gmail_service, 
                    limit=5
                )
                
            if not emails:
                st.warning("⚠️ No new emails found.")
                st.stop()

            for idx, email in enumerate(emails):
                st.markdown("---")
                st.markdown(f"### Email #{idx+1}")
                st.markdown(f"**From:** {email['from']}")
                st.markdown(f"**Subject:** {email['subject']}")
                st.markdown(f"**Snippet:** {email['snippet']}")
                st.markdown(f"**Body:** {email['body'][:500]}...")

                # Classification
                with st.spinner("Classifying email..."):
                    label = classifier.predict(email['body'])
                st.info(f"🧠 Classification: `{label.upper()}`")

                # Response generation for non-spam
                if label.lower() != "spam":
                    with st.spinner("Generating response..."):
                        suggested_reply = response_generator.generate_response(email['body'])
                    
                    user_reply = st.text_area(
                        "✍️ Suggested Reply:", 
                        suggested_reply, 
                        key=f"reply_{idx}"
                    )

                    if st.button("Send Reply", key=f"send_{idx}"):
                        with st.spinner("Sending reply..."):
                            responder_main.send_email_reply(
                                st.session_state.gmail_service,
                                email['threadId'], 
                                user_reply
                            )
                        st.success("✅ Reply sent!")

        except Exception as e:
            st.error(f"❌ Error processing emails: {str(e)}")

# ------------------------------
# Retrain Model Section
# ------------------------------
with st.expander("🧠 Train Custom Classifier", expanded=False):
    uploaded_file = st.file_uploader(
        "📄 Upload new training dataset (.csv)", 
        type=["csv"]
    )

    if uploaded_file:
        try:
            with open("training_data/sample_emails.csv", "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("✅ Training file uploaded!")
        except Exception as e:
            st.error(f"❌ File upload failed: {str(e)}")

    if st.button("Retrain Model"):
        try:
            with st.spinner("Retraining model..."):
                # Replace with actual training data loading
                texts = ["Your account has been hacked!", "Hello, how are you?"]
                labels = ["spam", "personal"]
                
                classifier.train(texts, labels)
            st.success("🧠 Model retrained successfully!")
        except Exception as e:
            st.error(f"❌ Retraining failed: {str(e)}")