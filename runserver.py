import os
from example_app.example_app import app

# Start a Flask development server with SSL support
# Adobe Sign requires the oauth redirect URL to start with "https"
if __name__ == "__main__":
    # Start a development HTTPS server with SSL support
    ssl_context = (app.root_path+'/server.crt', app.root_path+'/server.key')

    print()
    print("Point your browser to https://localhost:5000")
    print("Notice the 's' in 'https'")
    print()
    app.run(host='127.0.0.1',port=5000,
            debug = True, ssl_context=ssl_context)

