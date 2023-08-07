from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow


def uploadToGoogleDrive(pdf_file):
    # Set up Google Drive API credentials
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = None
    flow = InstalledAppFlow.from_client_secrets_file(
        'path/to/credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    # Initialize Google Drive API
    drive_service = build('drive', 'v3', credentials=creds)

    # Upload the PDF file to Google Drive
    media = MediaFileUpload(pdf_file, mimetype='application/pdf')
    file_metadata = {
        'name': 'web_crawler_report.pdf',
        'mimeType': 'application/pdf'
    }
    file = drive_service.files().create(
        body=file_metadata, media_body=media, fields='id').execute()

    print('File ID: %s' % file.get('id'))
