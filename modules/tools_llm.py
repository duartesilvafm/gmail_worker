import base64
import os
import json
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv


# load environment variables
load_dotenv()


# get scopes and credentials
client_id = os.getenv("GMAIL_CLIENT_ID")
client_secret = os.getenv("GMAIL_CLIENT_SECRET")
scopes = [
    "https://www.googleapis.com/auth/gmail.send", 
    "https://www.googleapis.com/auth/gmail.readonly", 
    "https://www.googleapis.com/auth/gmail.compose"
]


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
    scopes
)


# Save the credentials for the next run
creds = flow.run_local_server(port=0)
service = build("gmail", "v1", credentials=creds)


# Function to create a draft email
def create_draft(
        content:str, 
        to_sender: list = [],
        from_sender: list = ["me"],
        subject: str = "Automated Draft", 
        service: object = service):
    
    """
    Create a draft email in Gmail.

    Args:
        content (str): The content of the email draft.
        to_sender (list): The email address of the recipient.
        from_sender (list): The email address of the sender.
        subject (str): The subject of the email draft.
        service (object): The Gmail API service object.
    
    """
    try:
        # create gmail api client
        message = EmailMessage()

        message.set_content(content)

        message["To"] = to_sender
        message["From"] = from_sender
        message["Subject"] = subject

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"message": {"raw": encoded_message}}
        # pylint: disable=E1101
        draft = (
            service.users()
            .drafts()
            .create(userId="me", body=create_message)
            .execute()
        )

        print(f'Draft id: {draft["id"]}\nDraft message: {draft["message"]}')

    except HttpError as error:
        print(f"An error occurred: {error}")
        draft = None

    return draft


# Function send an email
def send_email(
        to_sender: list = [],
        from_sender: list = ["me"],
        subject: str = "Automated Draft",
        content: str = "This is an automated draft email",
        service: object = service
    ):

    """
    Send an email using the Gmail API.
    
    Args:
        to_sender (str): The email address of the recipient.
        from_sender (str): The email address of the sender.
        subject (str): The subject of the email.
        content (str): The content of the email.
        service (object): The Gmail API service object.
    """

    try:
        message = EmailMessage()

        message.set_content(content)

        message["To"] = to_sender
        message["From"] = from_sender
        message["Subject"] = subject

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}
        # pylint: disable=E1101
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        print(f'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(f"An error occurred: {error}")
        send_message = None
    return send_message


def get_email():
    pass


def delete_email():
    pass


def create_meeting():
    pass


def delete_meeting():
    pass


def get_meeting():
    pass


def handle_tool_call(message):

    for tool_call in message.tool_calls:

        # Extract the function arguments from the tool call
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if function_name == "create_draft":
            # Call the create_draft function with the arguments from the tool call
            response = create_draft(**arguments)
        elif function_name == "send_email":
            # Call the send_email function with the arguments from the tool call
            response = send_email(**arguments)
        else:
            raise ValueError(f"Unknown tool call: {tool_call.function.name}")

    # for the
    response = {
        "role": "tool",
        "content": json.dumps(arguments),
        "name": function_name,
        "tool_call_id": tool_call.id
    }
    return response


create_draft_function = {
    "name": "create_draft",
    "description": "Create a draft email",
    "parameters": {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The content of the email draft"
            },
            "to_sender": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "The email address of the recipient"
            },
            "from_sender": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "The email address of the sender"
            },
            "subject": {
                "type": "string",
                "description": "The subject of the email draft"
            }
        },
        "required": ["content", "to_sender", "from_sender", "subject"],
        "additionalProperties": False
    }
}

send_email_function = {
    "name": "send_email",
    "description": "Send an email",
    "parameters": {
        "type": "object",
        "properties": {
            "to_sender": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "The email address of the recipient"
            },
            "from_sender": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "The email address of the sender"
            },
            "subject": {
                "type": "string",
                "description": "The subject of the email"
            },
            "content": {
                "type": "string",
                "description": "The content of the email"
            }
        },
        "required": ["to_sender", "from_sender", "subject", "content"],
        "additionalProperties": False
    }
}

tools = [
    {
        "type": "function",
        "function": create_draft_function
    },
    {
        "type": "function",
        "function": send_email_function
    }
]