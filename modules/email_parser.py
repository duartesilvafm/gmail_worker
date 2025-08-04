import email 
import base64
import yaml
from pathlib import Path
from langchain.schema import Document
from bs4 import BeautifulSoup

def html_to_clean_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove all non-text elements
    for tag in soup(['script', 'style', 'a', 'button', 'img', 'nav', 'footer', 'header', 'form', 'svg']):
        tag.decompose()

    # Extract visible text
    text = soup.get_text(separator=' ', strip=True)
    return text


def write_document_to_markdown(doc: Document, output_path: str):
    # Prepare YAML frontmatter
    frontmatter = yaml.dump(doc.metadata, sort_keys=False)

    # Combine metadata and body
    markdown = f"---\n{frontmatter}---\n\n{doc.page_content.strip()}\n"

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)


def get_email_data(message_id, service):
  message = service.users().messages().get(userId='me', id=message_id, format='raw').execute()
  msg_str = base64.urlsafe_b64decode(message['raw'])
  email_msg = email.message_from_bytes(msg_str)
  body=None
  html=''

  email_subject = email_msg.get_all('Subject')
  from_sender = email_msg.get_all('From')
  to_recipient = email_msg.get_all('To')
  datetime_rx = email_msg.get_all('Date')  
  
  if email_msg.is_multipart():
      for part in email_msg.walk():
          content_type = part.get_content_type()
          disp = str(part.get('Content-Disposition'))
          # look for plain text parts, but skip attachments
          if part.get_content_charset() is None:
              # We cannot know the character set, so return decoded "something"
              body = part.get_payload(decode=True)
              continue
          if content_type == 'text/plain' and 'attachment' not in disp:
              charset = part.get_content_charset()
              # decode the base64 unicode bytestring into plain text
              body = part.get_payload(decode=True).decode(encoding=charset, errors="ignore")
              # if we've found the plain/text part, stop looping thru the parts
              break
          if content_type == 'text/html' and 'attachment' not in disp:
              charset = part.get_content_charset()
              html = part.get_payload(decode=True).decode(encoding=charset, errors="ignore")
              # if we've found the plain/text part, stop looping thru the parts
              break           
  else:
      # not multipart - i.e. plain text, no attachments
      content_type = email_msg.get_content_type()
      if email_msg.get_content_charset() is None:
          # We cannot know the character set, so return decoded "something"
          body = email_msg.get_payload(decode=True)
      else: 
          charset = email_msg.get_content_charset()
          if content_type == 'text/plain':
              body = email_msg.get_payload(decode=True).decode(encoding=charset, errors="ignore")
          if content_type == 'text/html':
              html = email_msg.get_payload(decode=True).decode(encoding=charset, errors="ignore")
  if body is not None:
      body = body.strip()
  else:
      body  = html_to_clean_text(html)
      body = body.strip()
  return body, from_sender, to_recipient, datetime_rx, email_subject 