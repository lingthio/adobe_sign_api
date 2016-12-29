Synopsis
========

This code example illustrates the use of the AdobeSign API
by implementing a simple Flask web application that:

- prepares a Document,
- shows that Document in an IFrame (AdobeSign Widget), and
- prompts the user to sign that Document.

| AdobeSign API documetation:
| https://secure.na1.echosign.com/public/docs/restapi/v5


Motivation
==========

I found that the API calls are well documented, but being new to this API,
I struggled trying to figure out which API calls to make and in what sequence.
I'm sharing this code example to provide a code illustration to other developers.

Though this code example is in Python (using the Flask application framework),
it illustrates the API for developers using other programming languages.


Code organization
=================
* ``adobe_sign_api/`` contains a simple wrapper for the AdobeSign API.
* ``example_app/`` contains a simple Flask application that calls the wrapper.
* ``runserver.py`` starts a development web server that serves the Flask application.


Example Python inteface to the Adobe Sign REST API
==================================================

The purpose of this code repository is to be an additinal information source
for developers wanting to interface to the Adobe Sign REST API.

I struggled a bit to make this work, and I'm publishing this code to save
other developers from this struggle.

As such is is NOT meant to be a fully functioning package and it will likely NOT be maintained,
beyond adding example functionality submitted by various contributors.

Though it's in Python, it probably serves developers of other programming languages too.


Installation
============
It is assumed that you have virtualenv and virtualenvwrapper installed and configured::

    # Clone this repository
    mkdir ~/dev
    git clone git@github.com:lingthio/adobe_sign_api.git adobe_sign_api

    # Create a virtualenv
    mkvirtualenv adobe_sign_api -p /full/path/to/python

    # Install required python packages (Flask and requests)
    cd ~/dev/adobe_sign_api
    pip install -r requirements.txt


Configuring Adobe Sign API Application
--------------------------------------------------
- Create an account at Adobe Sign Development Center and login: https://secure.na1.echosign.com/
- Navigate to ``API`` > ``Adobe Sign API`` > ``API Applications``.
- Add a new API Application (plus sign icon).
- Select this API Application
- Click on ``Configure OAuth for Application``.
- Take note of ``Client ID`` and ``Client Secret``.
- ``Redirect URI``: ``https://localhost:5000/adobe_sign/oauth_redirect``

    - This must start with ``https`` and must be served by our Example web application.

- Enable the appropriate ``Enabled Scopes``:

    - Enable ``user_login`` with modfier ``self``.
    - Enable ``widget_write`` with modifier ``account``.
    - Enable ``library_read`` with modifier ``account``.

- Click ``Save``.


Configuring the example web application
---------------------------------------
Copy the example settings to a local file::

    cd ~/dev/adobe_sign_api/example_app
    cp local_settings_example.py local_settings.py

Edit ``local_settings.py`` to reflect your Adobe Sign settings:

- ``ADOBE_SIGN_CLIENT_ID`` must reflect the Adobe Sign CLIENT_ID
- ``ADOBE_SIGN_CLIENT_SECRET`` must reflect the Adobe Sign CLIENT_SECRET


Starting the web application
============================
The Adobe Sign API requires that the authentication code request redirects to
a secure URL (HTTPS instead of HTTP). To avoid conflicts with existing ports,
we configured this HTTPS web application to run on port 5443.
::

    workon adobe_sign_api
    cd ~/dev/adobe_sign_api
    python runserver.py

You can now point your browser to: https://localhost:5433/


Access Tokens
-------------
Access Tokens are temporary tokens that are required to call the Adobe Sign API.

API calls are made in three steps:

1. Request an Authentication Code
2. Request an Access Token (using the Authentication Code)
3. Call the Adobe Sign API (using the Access Token)

1. Request an Authentication Code
---------------------------------
An Authentication Code request is made with an HTTPS call to::

    GET https://secure.na1.echosign.com/public/oauth
        ?response_type=code
        &client_id=...
        &redirect_uri=...                   # make sure to url-encode this
        &scope=...
        &state=...                          # any developer-supplied value

Adobe Sign authenticates the web application by offering the code through a redirect to
the pre-defined URL that points to your web server. In our case::

    https://localhost:5443/adobe_sign/oauth_redirect
        ?code=...
        &api_access_point=https://.../      # make sure to url-encode this
        &state=...                          # any developer-supplied value

The Authentication Code is returned in the query parameter ``code``

Note: Adobe Sign uses dynamic servers to process API requests from certain users.
The user assigned 'Access Point' is returned in the ``api_access_point`` query parameter
and must be used the base for this user's API calls.

In our example, the oauth url is constructed in adobe_sign/adobe_sign.py; make_oauth_url().

The request is initiated in example_app/templates/home.html; first ``<a ...>...</a>`` link.

The processing of the redirect response is done in example_app/example_app.py; oauth_redirect().

See https://secure.na1.echosign.com/public/static/oauthDoc.jsp

2. Request an Access Token
--------------------------
An Access Token request is made with an HTTPS call to::

    GET {api_access_point}oauth/token
        ?grant_type=authorization_code
        &client_id=...
        &client_secret=...
        &redirect_uri=...                   # make sure to url-encode this
        &code=...                           # Authentication code from previous step

The temporary Access Token is returned in the JSON response::

    {
        "token_type": "Bearer",
        "access_token": "...",
            ...
    }

In our example, this is done in adobe_sign/adobe_sign.py; get_access_token().

See https://secure.na1.echosign.com/public/static/oauthDoc.jsp


3. Call the Adobe Sign API
--------------------------
Since Adobe Sign uses dynamic servers to serve their users, the Access Token must
first be used to retrieve the API Access Point of a specific user.

Call a fixed URL to get the dynamic API Access Point with Access-Token in the header::

    # with Access-Token: ... in the header:
    GET https://api.echosign.com/api/rest/v5/base_uris

The dynamic Access Point is returned in as a JSON object::

    {
        "api_access_point": "...",
            ...
    }

Call the desired API with Access-Token in the header::

    # with Access-Token: ... in the header:
    GET {api_access_point}api/rest/v5/libraryDocuments

In our example, this is done in adobe_sign/adobe_sign.py; get_api_access_point().

See https://secure.na1.echosign.com/public/docs/restapi/v5


About Creating Widgets
----------------------
Note: The transient document must include an email form field. If not, Adobe Sign will add an extra page
to the PDF with a signature and email field.

Note: The email address will be verified, unless email address verification has been disabled.
Go to https://secure.na1.echosign.com/ > Account > Account Settings > Signature Preferences >
Widget Email Verification (near the bottom of this page).


Troubleshooting
---------------
If the ``Request new Access Token`` link displays this error message::

    Unable to authorize access because the client configuration is invalid: invalid_request

You need to check the following:

- example_app/local_settings.py: ADOBE_SIGN_CLIENT_ID is properly set
- example_app/local_settings.py: ADOBE_SIGN_CLIENT_SECRET is properly set
- Your ``Redirect URI`` in API Application configuration in Adobe Sign includes ``https://localhost:5443/adobe_sign/oauth_redirect``.


Contributors
============
Ling Thio - ling.thio AT gmail.com

Did you find this useful? Consider tipping me or sending me a thank you email!
