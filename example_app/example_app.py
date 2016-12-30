from flask import Flask, request, current_app, render_template, redirect, url_for
from adobe_sign_api import AdobeSignAPI

# Create a web application with Flask
app = Flask(__name__)

# Copy local_settings.py from local_settings_example.py
# Edit local_settings.py to reflect your CLIENT_ID and CLIENT_SECRET
app.config.from_pyfile('local_settings.py')    # Read example_app.local_settings.py

# Initialize the AdobeSign package
adobesign_api = AdobeSignAPI(
        app.config.get('ADOBE_SIGN_CLIENT_ID'),
        app.config.get('ADOBE_SIGN_CLIENT_SECRET'),
        app.config.get('ADOBE_SIGN_REDIRECT_URL'))


# Display the home page
@app.route('/')
def home_page():
    # This link will cause Adobe Sign to redirect to
    # 'https://localhost:5443/adobe_sign/oauth_redirect' with authentication information
    oauth_url = adobesign_api.make_oauth_url(
            'user_login:self+library_read:account+widget_write:account', # authorization scope
            '')                                                                 # developer-supplied state string

    # token will be None on the first visit, and will hold the access token on subsequent visits
    access_token = request.args.get('token')

    # Render the home page
    return render_template('home.html',
            oauth_url=oauth_url,
            access_token=access_token)



# Adobe Sign will redirect to this URL (https://localhost:5443/adobe_sign/oauth_redirect)
# in response to an authorization request (https://secure.na1.echosign.com/public/oauth).
@app.route('/adobe_sign/oauth_redirect')
def oauth_redirect():

    # Authentication info is passed in the GET query parameters
    # - code:              Authentication code
    # - api_access_point:  Points to the proper api server (https://secure.na1.echosign.com/)
    # - state:             Developer-supplied state string
    authorization_code = request.args.get('code')
    api_access_point = request.args.get('api_access_point')
    state = request.args.get('state')

    # Use authorization_code and api_access_point to retrieve an access token
    access_token = adobesign_api.get_access_token(authorization_code, api_access_point)
    assert(access_token)

    # Redirect back to the home page, but this time with the access token
    return redirect(url_for('home_page')+'?token='+access_token)


# Retrieve and render a list of Adobe Sign Library Documents
@app.route('/show_library_documents')
def show_library_documents():
    
    # Get access token from the URL query string
    access_token = request.args.get('token')
    
    # Use AdobeSign to retrieve a list of library documents
    if access_token:
        documents = adobesign_api.get_library_documents(access_token)
    else:
        documents = None

    # Render the list of documents
    return render_template('show_library_documents.html',
            documents=documents,
            access_token=access_token)


# Create and render an Adobe Sign Widget
@app.route('/show_iframe')
def show_iframe():
    # Get access token from the URL query string
    access_token = request.args.get('token')

    # Upload an example PDF with form fields as a transientDocument
    response = None
    path_and_filename = app.root_path + '/example.pdf'
    pdf_document_id = adobesign_api.create_transient_document(access_token, path_and_filename)

    # Create a widget using the transientDocument PDF and the libraryDocument form fields template
    completion_uri = 'https://localhost:5443'               # TODO: Implement properly
    email = 'someone@example.com'
    widget_creation_info = {
        # Specify Document
        "fileInfos": [
            {
                "transientDocumentId": pdf_document_id,
            }
        ],
        "name": 'OurCompany Contract with client X',
        "recipientSetInfos": [
            {
                "recipientSetMemberInfos": [
                    { "email": email },
                ],
                "recipientSetRole": 'SIGNER',
            },
        ],
        "signatureType": 'ESIGN',
        "signatureFlow": 'SENDER_SIGNATURE_NOT_REQUIRED',
        # Pre-fill form fields
        "mergeFieldInfo": [
            {
                "fieldName":    app.config.get('FIELD1_NAME',  'Name_Last'),
                "defaultValue": app.config.get('FIELD1_VALUE', 'Pre-filled Value One'),
            },
            {
                "fieldName":    app.config.get('FIELD2_NAME',  'Name_First'),
                "defaultValue": app.config.get('FIELD2_VALUE', 'Pre-filled Value Two'),
            },
            {
                "fieldName":    app.config.get('FIELD3_NAME',  'Address_1'),
                "defaultValue": app.config.get('FIELD3_VALUE', 'Pre-filled Value Three'),
            },
        ],
        # Redirect to completion URL after signing
        "widgetCompletionInfo": {
            "url": completion_uri,
            "deframe": True,
            "delay": 0
        },
    }
    widget = adobesign_api.create_widget(access_token, widget_creation_info)

    # Render the list of documents
    return render_template('show_iframe.html',
            widget=widget,
            access_token=access_token)

