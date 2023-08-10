from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
import os
import requests
import pickle

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://mail.google.com/', 
          'https://www.googleapis.com/auth/photoslibrary', 
          'https://www.googleapis.com/auth/photoslibrary.sharing']


def get_service():
    print("Getting service...")
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    try:
        service = build('gmail', 'v1', credentials=creds)
        print("Service created successfully")
        return service, creds
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def list_messages(service, user_id='me'):
    try:
        response = service.users().messages().list(userId=user_id).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, pageToken=page_token).execute()
            messages.extend(response['messages'])

        return messages
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_message(service, msg_id, user_id='me'):
    try:
        return service.users().messages().get(userId=user_id, id=msg_id).execute()
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_attachments(service, message):
    """Get and store the photo attachments."""
    # print('in get_attachments')
    if 'parts' in message['payload']:
        # print('testpoint1')
        for part in message['payload']['parts']:
            mime_type = part['mimeType']
            if part['filename'] and (mime_type.startswith('image/') or mime_type.startswith('application/')):
                if 'data' in part['body']:
                    data = part['body']['data']
                elif 'attachmentId' in part['body']:
                    att_id = part['body']['attachmentId']
                    att = service.users().messages().attachments().get(userId='me', messageId=message['id'], id=att_id).execute()
                    data = att['data']
                else:
                    print(f"No data or id in part: {part}")
                    continue
                file_data = base64.urlsafe_b64decode(data)
                file_path = os.path.join('photos', part['filename'])

                with open(file_path, 'wb') as f:
                    f.write(file_data)



def upload_to_photos(file_path, creds):
    """Upload the photo to Google Photos."""
    url = 'https://photoslibrary.googleapis.com/v1/uploads'
    headers = {
        'Authorization': 'Bearer ' + creds.token,
        'Content-type': 'application/octet-stream',
        'X-Goog-Upload-File-Name': os.path.basename(file_path),
        'X-Goog-Upload-Protocol': 'raw',
    }
    img = open(file_path, 'rb').read()
    response = requests.post(url, data=img, headers=headers)
    return response.content  # This is the upload token.


def create_media_item(upload_token, creds, album_id=None):
    """Create a media item in the user's Google Photos account."""
    url = 'https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate'
    headers = {
        'Authorization': 'Bearer ' + creds.token,
        'Content-type': 'application/json',
    }
    body = {
        'newMediaItems': [
            {
                'description': 'Uploaded by my script',
                'simpleMediaItem': {
                    'uploadToken': upload_token.decode(),
                }
            }
        ],
    }
    if album_id:
        body['albumId'] = album_id
    response = requests.post(url, json=body, headers=headers)
    return response.json()


def delete_message(service, msg_id, user_id='me'):
    try:
        service.users().messages().delete(userId=user_id, id=msg_id).execute()
    except Exception as e:
        print(f"An error occurred: {e}")



def main():
    service, creds = get_service()

    # Get the list of messages
    messages = list_messages(service)

    # Initialize counters for the number of photos uploaded and messages processed
    photos_uploaded_count = 0
    messages_processed_count = 0

    # For each message
    for msg in messages:
        # Get the message
        message = get_message(service, msg['id'])
        print(f"processing message: {messages_processed_count+1}")
        # Get and store the attachments
        get_attachments(service, message)

        # For each attachment
        for filename in os.listdir('photos'):
            # Upload the photo to Google Photos
            upload_token = upload_to_photos(os.path.join('photos', filename), creds)

            # Create a media item
            create_media_item(upload_token, creds)

            # Delete the file
            os.remove(os.path.join('photos', filename))

            # Increment the counter
            photos_uploaded_count += 1

            # Print the number of photos uploaded so far
            print(f"{photos_uploaded_count} new images saved to Google Photos")

        # Increment the messages processed counter
        messages_processed_count += 1

        # Delete the message
        delete_message(service, msg['id'])

    # Print the total number of photos uploaded and messages processed
    print(f"{photos_uploaded_count} pictures added to Google Photos from {messages_processed_count} messages")

if __name__ == '__main__':
    main()
