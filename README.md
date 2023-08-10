# gmail2photos
Auto transfer from Gmail to Google Photos 

In the Google API, you don't directly use your Gmail username and password. Instead, you use OAuth 2.0 for authentication and authorization. This involves creating a project in the Google Cloud Console, enabling the necessary APIs (Gmail, Google Photos), and creating credentials.

Here are the steps to create credentials:

Go to the Google Cloud Console.
https://console.cloud.google.com/
Create a new project or select an existing one.

Enable the Gmail API and Google Photos API with the following scopes for your project.

  Photos Library API
    /auth/photoslibrary
    /auth/photoslibrary.sharing

  Gmail API
    https://mail.google.com/

Go to the "Credentials" page.
Click "Create Credentials" and select "OAuth client ID".
Configure the OAuth consent screen.
For the application type, select "Desktop app".
Click "Create". The console will provide you with a client ID and client secret.
After you've created your credentials, download them as a JSON file. Rename this file to credentials.json and place it in the same directory as your Python script. The get_service function in the script will use this file to authenticate your application and authorize it to access your data.

The first time you run the script, it will open a new window in your web browser and ask you to authorize the application to access your data. After you authorize the application, it will store your access and refresh tokens in a file named token.pickle. In subsequent runs, the script will use these tokens for authentication, so you won't have to authorize the application again.
