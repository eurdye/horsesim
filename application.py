'''
DEAD HORSE

Hacker beware, here be dragons.

This code is made out of snippets from ChatGPT duct-taped together. I did some things very wrong because this is my first big game like this and I wasn't thinking ahead. Look, this isn't Finnegan's Wake, it's a text adventure about a horse who died. It's hacky and it works.
'''

from deadhorse import user_input_parser
from flask import Flask, render_template, session, request, redirect, url_for
import ephem
from collections import deque
import csv, sys
import os
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = 'horsae'  # Change this to a secret key for secure sessions
app.config['SESSION_COOKIE_MAX_SIZE'] = 4096  # Set a maximum size for the session cookie

@app.route('/')

def home():
    # Retrieve the response from the session or default to an empty string
    response_key = 'response'
    response = session.get(response_key, '')

    # Retrieve the list of previous responses from the session or initialize an empty list
    previous_responses_key = 'previous_responses'
    previous_responses = session.get(previous_responses_key, [])

    # Keep only the last 40 responses
    previous_responses = previous_responses[-40:]
    session['previous_responses'] = previous_responses
    return render_template('index.html', response=response, previous_responses=previous_responses)

from collections import deque

@app.route('/update_input', methods=['POST'])
def update_input():
    # Get the user input from the text box
    user_input = request.form.get('user_input', '')

    # Use a fixed key for the response
    response_key = 'response'

    # Use a fixed key for the list of previous responses
    previous_responses_key = 'previous_responses'
    
    # Use a fixed key for the clear command
    clear_command = 'clear'
   
    # Check if the user input is the clear command
    if user_input.lower() == clear_command:
        # Clear the screen by removing all previous responses
        session[previous_responses_key] = []
        return redirect(url_for('home'))
   
    session[response_key] = user_input_parser(user_input.lower())
    # Append the current response to the list of previous responses
    previous_responses = session.get(previous_responses_key, deque(maxlen=40))
    previous_responses.append("> " + f'{user_input}')
    previous_responses.append(session[response_key])
    session[previous_responses_key] = list(previous_responses)

    return redirect(url_for('home'))

# Create the application object
application = app

if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0', port=5000)

