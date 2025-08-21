import datetime
import os.path
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from markdownify import markdownify as md
from modules import email_parser as em

# get scopes and credentials
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", 
          "https://www.googleapis.com/auth/calendar.readonly"]

# Load environment variables
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


"""
Authenticate and build the Gmail service to download emails
"""


# Call the Gmail API
service = build("gmail", "v1", credentials=creds)
results = service.users().messages().list(userId="me", labelIds=["INBOX"]).execute()
messages = results.get("messages", [])
print(f"Number of messages: {len(messages)}")

# path variable
path_gmail= "google/gmail/"

# path to save emails
if not os.path.exists(path_gmail):
    os.makedirs(path_gmail)

# save as a list all the gmail documents
gmail_docs = []

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
    body, from_sender, to_recipient, date, email_subject = em.get_email_data(msg["id"], service)
    
    # Load the markdown file and print the content in markdown
    if not os.path.exists("emails"):
        os.makedirs("emails")

    doc = Document(
        page_content=body,
        metadata={
            "category": "email",
            "source": "gmail",
            "id": msg["id"],
            "from": ', '.join(from_sender),
            "to": ', '.join(to_recipient),
            "date": ', '.join(date),
            "subject": ', '.join(email_subject)
        }
    )

    # write to markdown
    output_path = os.path.join(path_gmail, f"{msg['id']}.md")    
    em.write_document_to_markdown(doc, output_path)
    gmail_docs.append(doc)


"""
BUILD SERVICE TO EXTRACT CALENDAR EVENTS
"""


# Call the Gmail API
service = build("calendar", "v3", credentials=creds)
time_min = (datetime.datetime.now() - datetime.timedelta(days=60)).isoformat() + 'Z'  # RFC3339 UTC "now"
time_max = (datetime.datetime.now() + datetime.timedelta(days=60)).isoformat() + 'Z'
path_calendar = "google/calendar/"

print(time_min, time_max)

# Create the directory if it doesn't exist
if not os.path.exists(path_calendar):
    os.makedirs(path_calendar)

# List the next 500 events from the primary calendar
events = service.events().list(
    calendarId='primary',
    timeMin=time_min,
    timeMax=time_max,
    maxResults=500
).execute()

# event documents
calendar_docs = []

# length of number of events
for event in events.get('items', []):

    # retrieve instances of the event
    instances = service.events().instances(
        calendarId='primary', 
        eventId=event['id'],
        timeMax=time_max,
        timeMin=time_min,
        maxResults=500,
    ).execute()

    if not instances.get('items'):
        print(f"No instances found for event {event['id']}")
        continue

    # iterate through the instances of the event
    for instance in instances.get('items', []):
        # Extract event details for each instance
        instance_id = instance['id']
        instance_summary = instance.get('summary', 'No Summary')
        instance_start = instance['start'].get('dateTime', instance['start'].get('date'))
        instance_end = instance['end'].get('dateTime', instance['end'].get('date'))

        # docstring for the event instance
        docstring = f"Event ID: {instance_id}\n" \
                    f"Summary: {instance_summary}\n" \
                    f"Start: {instance_start}\n" \
                    f"End: {instance_end}\n" \
                    f"Description: {instance.get('description', 'No Description')}\n" \
                    f"Location: {instance.get('location', 'No Location')}\n" \
                    f"Attendees: {', '.join([attendee['email'] for attendee in instance.get('attendees', [])]) if 'attendees' in instance else 'No Attendees'}\n"

        # Create a document for the calendar event instance
        doc_instance = Document(
            page_content=docstring,
            metadata={
                "category": "calendar",
                "source": "google_calendar",
                "id": instance_id,
                "event_id": event['id'],
                "event_summary": event.get('summary', 'No Title'),
                "instance_start": instance_start,
                "instance_end": instance_end,
            }
        )

        # write to markdown
        calendar_docs.append(doc_instance)
        output_path = os.path.join(path_calendar, f"{instance_id}.md")
        em.write_document_to_markdown(doc_instance, output_path)


# save the documents into one list
all_docs = gmail_docs + calendar_docs


"""
CREATE VECTORSTORE FROM DOCUMENTS
"""

# text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, 
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", ""]
)

# split into chunks
chunks = text_splitter.split_documents(all_docs)
print(f"Total number of chunks: {len(chunks)}")

# use hugging face embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db_name = "vector_db/"

# if the vector store already exists, delete it
if os.path.exists(db_name):
    Chroma(persist_directory=db_name, embedding_function=embeddings).delete_collection()
else:
    print(f"Path: {db_name} doesnt exist")


# Create vectorstore
vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=db_name)
print(f"Vectorstore created with {vectorstore._collection.count()} documents")