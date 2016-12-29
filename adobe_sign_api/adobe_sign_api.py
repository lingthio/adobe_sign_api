"""
Copyright 2016, SolidBuilds.com. All rights reserved.
Author: Ling Thio, ling.thio@gmail.com
"""

from __future__ import print_function
import requests
import json

LOCAL_DEBUG = False                      # Print local debug info or not
API_BASE_URL = 'api/rest/v5/'


# The AdobeSign class offers access to the Adobe Sign REST API version 5
class AdobeSignAPI(object):

    # Creates an instance of the AdobeSign class.
    # - client_id:     See Adobe Sign > API > API Applications > YOURAPP > Configure OAuth for Application
    # - client_secret: See Adobe Sign > API > API Applications > YOURAPP > Configure OAuth for Application
    def __init__(self, client_id='', client_secret='', oauth_redirect_url=''):
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_redirect_url = oauth_redirect_url
        self.api_access_point = None
        self.base_uri = None
        pass


    def make_oauth_url(self, scope, state=''):
        # Start with the Adobe Sign OAuth URL
        oauth_url = 'https://secure.na1.echosign.com/public/oauth?response_type=code'
        # Add the Client ID
        oauth_url += '&client_id=' + self.client_id
        # Add the Oauth redirect url
        oauth_url += '&redirect_uri=' + requests.utils.quote(self.oauth_redirect_url)
        # Add the scope
        oauth_url += '&scope=' + scope
        # Add developer-supplied state string
        oauth_url += '&state=' + state
        return oauth_url

    # Uses the client ID, client secret and authorization code to return a temporary access token.
    # - authorization code: The value of the 'code' parameter in the OAuth callback URL
    # - redirect_uri:  Must exactly match one of the Redirect URIs configured in
    #                  Adobe Sign > API > API Applications > YOURAPP > Configure OAuth for Application
    # Returns the access_token if the parameters are valid.
    # Returns '' otherwise.
    def get_access_token(self, authorization_code, api_access_point):
        self.authorization_code = authorization_code
        self.api_access_point = api_access_point

        access_token = ''
        if self.authorization_code and self.api_access_point:
            # Use api_access_point with the authorization code to retrieve tokens
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            payload = {
                'code': self.authorization_code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.oauth_redirect_url,
                'grant_type': 'authorization_code',
            }

            # Call the Adobe Sign API
            url = self.api_access_point + 'oauth/token'
            response = requests.post(url, headers=headers, data=payload, allow_redirects=False)

            # Process the response
            if response.status_code in (200, 201):
                data = response.json()
                access_token = data.get('access_token')
            else:
                print('AdobeSign.get_access_token() failed.')
                print('response_body:', response.text)

        if LOCAL_DEBUG:
            print('access_token:', access_token)
        return access_token


    # Create a transientDocument by uploading a PDF file to Adobe Sign
    # - path_and_filename: Full path and filename to the PDF file
    # Returns the transient document ID on success.
    # Returns None otherwise.
    def create_transient_document(self, access_token, path_and_filename):
        transient_document_id = None
        if access_token:
            headers = {
                'Access-Token': access_token,
            }

            # upload file as part of a 3-part multipart-encoded payload
            mime_type = 'application/pdf'
            file = open(path_and_filename, 'rb')
            files = {
                'File-Name': ('', ''),          # Part 1
                'Mime-Type': ('', mime_type),   # Part 2
                'File': file,                   # Part 3
            }

            # Call the Adobe Sign API
            url = self.get_api_base_url(access_token) + 'transientDocuments'  # https://api.na1.echosign.com/api/rest/v5/...
            response = requests.post(url, headers=headers, files=files)

            # Process the response
            if response.status_code in (200, 201):
                response_body = response.json()
                transient_document_id = response_body.get('transientDocumentId')
            else:
                print('AdobeSign.upload_transient_document() failed.')
                print('response_body:', response.text)

        if LOCAL_DEBUG:
            print('transient_document_id =', transient_document_id)
        return transient_document_id


    # Get a list of library documents.
    # Returns a list of library document information records on success.
    # Returns None otherwise.
    def get_library_documents(self, access_token):
        library_documents = None

        # Retrieve a list of library documents
        if access_token:
            headers = {
                'Access-Token': access_token,
            }

            # Call the Adobe Sign API
            url = self.get_api_base_url(access_token) + 'libraryDocuments'    # https://api.na1.echosign.com/api/rest/v5/...
            response = requests.get(url, headers=headers)

            # Process the response
            if response.status_code in (200, 201):
                response_body = response.json()
                library_documents = response_body['libraryDocumentList']
            else:
                print('AdobeSign.get_library_documents() failed.')
                print('response_body:', response.text)
                
        return library_documents


    # Find a library document by document name.
    # Returns the library document ID on success.
    # Returns None otherwise.
    def find_library_document_by_name(self, library_documents, document_name):
        library_document_id = None
        if library_documents:
            for library_document in library_documents:
                if library_document['name'] == document_name:
                    library_document_id = library_document['libraryDocumentId']

        if LOCAL_DEBUG:
            print('library_document_id =', library_document_id)
        return library_document_id


    # Creates an Adobe Sign Widget from a transient document ID (contents) and
    # a library document ID (form fields)
    # An Adobe Sign Widget is an online form that allows the end-user to sign a PDF document.
    # Returns an instance of AdobeSignWidget on success.
    # Returns None otherwise.
    def create_widget(self, access_token, widget_creation_info):
        widget = None

        if access_token:
            payload = {
                "widgetCreationInfo": widget_creation_info
            }

            # Call the Adobe Sign API
            call_response = self.call_adobe_sign_api_post(access_token, 'widgets', payload)

            # Process the response
            if call_response:
                widget = AdobeSignWidget()
                widget.widget_id = call_response.get('widgetId')
                widget.javascript = call_response.get('javascript')
                widget.next_page_embedded_code = call_response.get('nextPageEmbeddedCode')
                widget.next_page_url = call_response.get('nextPageUrl')
                widget.url = call_response.get('url')
            else:
                print('AdobeSign.create_widget() failed.')

        return widget


    # Calls the Adobe Sign API at endpoint 'endpoint_url'.
    # Returns a python object on success.
    # Returns None otherwise.
    def call_adobe_sign_api_post(self, access_token, endpoint_url, payload):

        if access_token:
            # Create a widget with a document and a form fields template
            headers = {
                'Access-Token': access_token,
                'Content-Type': 'application/json',
            }

            # Call the Adobe Sign API: https://api.na1.echosign.com/api/rest/v5/{endpoint_url}
            url = self.get_api_base_url(access_token) + endpoint_url
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if LOCAL_DEBUG:
                print('POST', url, 'returned', response.status_code)

            # Process the response
            if response.status_code in (200, 201):
                call_response = response.json()
            else:
                print("AdobeSign.call_adobe_sign_api_post('"+endpoint_url+"') failed.")
                print('response_body:', response.text)
                call_response = None

        return call_response


    # Returns the api_access_point from the token on success.
    # Returns None otherwise.
    def get_api_access_point(self, access_token):
        # Don't bother retrieving it if we already retrieved it previously
        if self.api_access_point:
            return self.api_access_point

        # Retrieve a the base URIs
        if access_token:
            headers = {
                'Access-Token': access_token,
            }

            # Call the Adobe Sign API
            url = 'https://api.echosign.com/api/rest/v5/base_uris'
            response = requests.get(url, headers=headers)

            # Process the response
            if response.status_code in (200, 201):
                response_body = response.json()
                self.api_access_point = response_body['api_access_point']
            else:
                print('AdobeSign.get_base_uri() failed.')
                print('response_body:', response.text)

        return self.api_access_point


    # Returns the api_access_point + 'api/rest/v5/'
    def get_api_base_url(self, token):
        api_base_url = self.get_api_access_point(token) + API_BASE_URL  # https://api.na1.echosign.com/api/rest/v5/
        return api_base_url


# This class holds the Adobe Sign Widget information.
# It's used as a return value from the AdobeSign.create_widget() method.
class AdobeSignWidget(object):
    def __init__(self):
        self.widget_id = None
        self.javascript = ''
        self.next_page_embedded_code = ''
        self.next_page_url = ''
        self.url = ''
