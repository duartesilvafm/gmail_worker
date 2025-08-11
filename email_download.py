import os.path
from markdownify import markdownify as md
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from modules import email_parser as em
from dotenv import load_dotenv
from langchain.schema import Document

# get scopes and credentials
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
load_dotenv()

# Load client ID and secret from environment variables
client_id = os.getenv("GMAIL_CLIENT_ID")
client_secret = os.getenv("GMAIL_CLIENT_SECRET")

# create installed app flow
flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    },
    SCOPES
)

# Save the credentials for the next run
creds = flow.run_local_server(port=0)

# Call the Gmail API
service = build("gmail", "v1", credentials=creds)
results = service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=1000).execute()
messages = results.get("messages", [])
print(len(messages))

# List messages from google API
for message in messages:

    payload = {
        "userId": "me",
        "id": message["id"],
        "format": "raw"
    }

    try:
        # Get the message details
        msg = service.users().messages().get(**payload).execute()
    except HttpError as error:
        print(f"An error occurred: {error}")
        msg = None

    # if msg is None
    body, from_sender, to_recipient, datetime, email_subject = em.get_email_data(msg["id"], service)
    
    # Load the markdown file and print the content in markdown
    if not os.path.exists("emails"):
        os.makedirs("emails")

    doc = Document(
        page_content=body,
        metadata={
            "from": from_sender,
            "to": to_recipient,
            "date": datetime,
            "subject": email_subject
        }
    )

    # write to markdown
    em.write_document_to_markdown(doc, f"emails/{msg['id']}.md")