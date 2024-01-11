from deadhorse import user_input_parser
from flask import Flask, render_template, session, request, redirect, url_for
import ephem

app = Flask(__name__)
app.secret_key = 'horsae' # Change this to a secret key for secure sessions

@app.route('/')
def home():
    # Retrieve the user input from the session or default to an empty string
    user_input_key = 'user_input'
    user_input = session.get(user_input_key, '')

    # Retrieve the response from the session or default to an empty string
    response_key = 'response'
    response = session.get(response_key, '')

    # Retrieve the list of previous responses from the session or initialize an empty list
    previous_responses_key = 'previous_responses'
    previous_responses = session.get(previous_responses_key, [])

    return render_template('index.html', user_input=user_input, response=response, previous_responses=previous_responses)

@app.route('/update_input', methods=['POST'])
def update_input():
    # Get the user input from the text box
    user_input = request.form.get('user_input', '')

    # Use a fixed key for user input
    user_input_key = 'user_input'

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
        # Clear the current response
        session[response_key] = ''
    else:
        session[response_key] = user_input_parser(user_input.lower())

    # Append the current response to the list of previous responses
    previous_responses = session.get(previous_responses_key, [])
    previous_responses.append("> " + f'{user_input}')
    previous_responses.append(session[response_key])
    session[previous_responses_key] = previous_responses

    return redirect(url_for('home'))

import os
from flask import send_from_directory

if __name__ == '__main__':
    app.run(debug=True)
