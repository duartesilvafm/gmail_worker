import base64
import os
import json
import datetime
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
    "https://www.googleapis.com/auth/gmail.compose",
    'https://www.googleapis.com/auth/calendar'
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
calendar_service = build('calendar', 'v3', credentials=creds)

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


def move_email():
    pass


def delete_email():
    pass


def get_event(
        query: str="", 
        service: object = calendar_service
    ):

    """
    Get events from the user's calendar.

    Args:
        query (str): The query to search for events.
        service (object): The Calendar API service object.
    Returns:
        list: A list of events matching the query.
    """
    try:
        events_id = service.events().list(
            calendarId='primary', 
            maxResults=1, 
            q=query,
            orderBy='startTime'
            ).execute()
        events = events_id.get('items', [])
        return events
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


def create_event(
        summary: str = "Test Event",
        location: str = "Virtual",
        description: str = "This is a test event",
        start: dict = {datetime.datetime.now() + datetime.timedelta(hours=1), ""},
        end: dict = {datetime.datetime.now() + datetime.timedelta(hours=1), ""},
        recurrence: list = ["RRULE:FREQ=DAILY;COUNT=2"],
        attendees: list = [{"email": "me"}],
        reminders: dict = {'userDefault': True},
        service: object = calendar_service
    ):
    """
    Create an event in the user's calendar.
    Args:
        summary (str): The summary of the event.
        location (str): The location of the event.
        description (str): The description of the event.
        start (dict): The start date and time of the event in ISO format.
        end (dict): The end date and time of the event in ISO format.
        recurrence (list): The recurrence rules for the event.
        attendees (list): The list of attendees for the event.
        reminders (dict): The reminders for the event.
        service (object): The Calendar API service object.
    """

    events = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {
            "dateTime": start.get("dateTime", datetime.datetime.now().isoformat()),
            "timeZone": start.get("timeZone", "UTC")
        },
        "end": {            
            "dateTime": end.get("dateTime", datetime.datetime.now().isoformat()),
            "timeZone": end.get("timeZone", "UTC")
        },
        "recurrence": recurrence,
        "attendees": attendees,
        "reminders": reminders
    }

    event = service.events().insert(
        calendarId='primary',
        body=events
    ).execute()
    print(f"Event created: {event.get('htmlLink')}")


def update_event(
        search_string: str = "",
        service: object = calendar_service,
        **kwargs
    ):
    """
    Update an event in the user's calendar.
    Args:
        query (str): The query to find the event to update.
        service (object): The Calendar API service object.
        **kwargs: The fields to update in the event.
    Returns:
        None
    """

    event = get_event(query=search_string)
    if not event:
        print("No event found with the given query.")
        return
    
    event = {
        **kwargs
    }

    update = service.events().update(
        calendarId='primary',
        eventId=event['id'],
        body=event
    ).execute()
    print(f"Event updated: {update.get('htmlLink')}")


def delete_event(query: str = "", service: object = calendar_service):
    """
    Delete an event from the user's calendar.

    Args:
        query (str): The query to find the event to delete.
        service (object): The Calendar API service object.
    Returns:
        None
    """
    event, event_id = get_event(query=query, service=service)
    if not event:
        print("No event found with the given query.")
        return
    
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        print(f"Event with ID {event_id} deleted successfully.")
    except HttpError as error:
        print(f"An error occurred: {error}")


def handle_tool_call(message):
    """
    Handle tool calls from the model's response.
    Args:
        message (object): The message containing tool calls.
    Returns:
        dict: The response from the tool call.
    """


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
        elif function_name == "create_event":
            # Call the create_event function with the arguments from the tool call
            response = create_event(**arguments)
        elif function_name == "update_event":
            # Call the update_event function with the arguments from the tool call
            response = update_event(**arguments)
        elif function_name == "delete_event":
            # Call the delete_event function with the arguments from the tool call
            response = delete_event(**arguments)
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

create_event_function = {
    "name": "create_event",
    "description": "Create an event in the user's calendar",
    "parameters": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "The summary of the event"
            },
            "location": {
                "type": "string",
                "description": "The location of the event"
            },
            "description": {
                "type": "string",
                "description": "The description of the event"
            },
            "start": {
                "type": "object",
                "properties": {
                    "dateTime": {
                        "type": "string",
                        "description": "The start date and time of the event in ISO format"
                    },
                    "timeZone": {
                        "type": "string",
                        "description": "The time zone of the start date and time"
                    }
                },
                "required": ["dateTime", "timeZone"],
                "description": "The start date and time of the event"
            },
            "end": {
                "type": "object",
                "properties": {
                    "dateTime": {
                        "type": "string",
                        "description": "The end date and time of the event in ISO format"
                    },
                    "timeZone": {
                        "type": "string",
                        "description": "The time zone of the end date and time"
                    }
                },
                "required": ["dateTime", "timeZone"],
                "description": "The end date and time of the event"
            },
            "recurrence": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "The recurrence rules for the event"
            },
            "attendees": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "The email address of the attendee"
                        }
                    },
                    "required": ["email"],
                    "description": "The list of attendees for the event"
                }
            },
            "reminders": {
                "type": "object",
                "properties": {
                    "useDefault": {
                        "type": "boolean",
                        "description": "Whether to use the default reminders"
                    },
                    "overrides": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "method": {
                                    "type": "string",
                                    "description": "The method of the reminder (e.g., email, popup)"
                                },
                                "minutes": {
                                    "type": "integer",
                                    "description": "The number of minutes before the event to send the reminder"
                                }
                            },
                            "required": ["method", "minutes"],
                            "description": "The overrides for the reminders"
                        }
                    }
                },
                "required": ["useDefault"],
                "description": "The reminders for the event"
            }
        },
        "required": ["summary", "location", "description", "start", "end", "recurrence", "attendees", "reminders"],
        "additionalProperties": False
    }
}

update_event_function = {
    "name": "update_event",
    "description": "Update an event in the user's calendar",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The query to find the event to update"
            },
            "summary": {
                "type": "string",
                "description": "The new summary of the event"
            },
            "location": {
                "type": "string",
                "description": "The new location of the event"
            },
            "description": {
                "type": "string",
                "description": "The new description of the event"
            },
            "start": {
                "type": "object",
                "properties": {
                    "dateTime": {
                        "type": "string",
                        "description": "The new start date and time of the event in ISO format"
                    },
                    "timeZone": {
                        "type": "string",
                        "description": "The time zone of the new start date and time"
                    }
                },
                "required": ["dateTime", "timeZone"],
                "description": "The new start date and time of the event"
            },
            "end": {
                "type": "object",
                "properties": {
                    "dateTime": {
                        "type": "string",
                        "description": "The new end date and time of the event in ISO format"
                    },
                    "timeZone": {
                        "type": "string",
                        "description": "The time zone of the new end date and time"
                    }
                },
                "required": ["dateTime", "timeZone"],
                "description": "The new end date and time of the event"
            },
            "recurrence": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "The new recurrence rules for the event"
            },
            "attendees": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "The email address of the attendee"
                        }
                    },
                    "required": ["email"],
                    "description": "The new list of attendees for the event"
                }
            },
            "reminders": {
                "type": "object",
                "properties": {
                    "useDefault": {
                        "type": "boolean",
                        "description": "Whether to use the default reminders"
                    },
                    "overrides": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "method": {
                                    "type": "string",
                                    "description": "The method of the reminder (e.g., email, popup)"
                                },
                                "minutes": {
                                    "type": "integer",
                                    "description": "The number of minutes before the event to send the reminder"
                                }
                            },
                            "required": ["method", "minutes"],
                            "description": "The new overrides for the reminders"
                        }
                    }
                },
                "required": ["useDefault"],
                "description": "The new reminders for the event"
            }
        },
        "required": ["query"],
        "additionalProperties": True
    }
}

delete_event_function = {
    "name": "delete_event",
    "description": "Delete an event from the user's calendar",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The query to find the event to delete"
            }
        },
        "required": ["query"],
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
    },
    {
        "type": "function",
        "function": create_event_function
    },
    {
        "type": "function",
        "function": update_event_function
    },
    {
        "type": "function",
        "function": delete_event_function
    }
]