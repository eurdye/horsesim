from flask import Flask, session
import ephem

def introspect_action(session, user_input):
    quests = session.setdefault('quests', {'introspect': 0})
    current_location = session.setdefault('location', {'x': 6, 'y': 7})
    if quests['introspect'] == 1 and current_location['x'] == 6 and current_location['y'] == 7:
        quests['introspect'] = 1
        return "Who are you? A fragile equine body lies heaped beneath you. You do not remember these muscles, this skin. You remember an argument. Fighting. A loss. Feelings, only vague, receding from you even now as your gaze drifts out over the endless sea... \n\nYou think you should take a LOOK around."
    elif quests['introspect'] == 0 and current_location['x'] == 6 and current_location['y'] == 6:
        return "It's awfully difficult to introspect on the city streets. The heat of the city gets to your pounding brain, throbs your sweaty forehead. Better go to the BEACH."

def status_action(session, user_input):
    return session.get('quests', {})

def look_action(session, user_input):
    current_location = session.setdefault('location', {'x': 6, 'y': 7})
    if current_location['x'] == 6 and current_location['y'] == 7:
        return '''You are on the Beach. Before you stretches the Endless Ocean\'s purple waves, pounding rhythmically against the shore.
                   Nearby is the PIER, the GROTTO, and the TOWN.'''
    elif current_location['x'] == 1 and current_location['y'] == 0:
        return '''You are in Slime City center, baby. Hustle, bustle, and some of that old-school funk.
                   Nearby, you see the SHOP, the CASINO, your HOME, the TRAIN, and the BEACH.'''
    else:
        return "You are in an unknown location."

# ... (other functions remain unchanged)
def where_action(session, user_input):
    return session.get('location', {})

def go_action(session, user_input, direction):
    current_location = session.setdefault('location', {'x': 6, 'y': 7})
    prev_location = dict(current_location)  # Store previous location for comparison
    if direction == 'north':
        current_location['y'] -= 1
    elif direction == 'south':
        current_location['y'] += 1
    elif direction == 'east':
        current_location['x'] += 1
    elif direction == 'west':
        current_location['x'] -= 1
    else:
        return "ERROR: No direction specified.\nUse \'go [north/south/east/west]\' to move in the specified direction."
    session['location'] = current_location
    if prev_location != current_location:
        return f'You head {direction}\n\n' + look_action(session, user_input)
    else:
        return f'Already at {direction}'

# Help command lists possible actions
def help_action(session, user_input):
    #return """COMMAND LIST:\nlook\nlook [object]\nget [object]\ngo [north, south, east, west]\nintrospect\ntalk [being]"""
    action_list = list(action_dict.keys())
    print_actions = lambda keys: '\n'.join(keys)
    return ("COMMAND LIST:\n"+print_actions(action_list))

# Find current moon phase
def moon_action(session, user_input):
    observer = ephem.Observer()
    moon = ephem.Moon()

    # Set the observer's location (latitude and longitude)
    observer.lat = '34.135559'  # Replace with your latitude
    observer.lon = '-116.054169'  # Replace with your longitude

    # Compute the moon's phase
    moon.compute(observer)
    # Determine the moon phase
    phase_angle = moon.phase % 360

    moon_response = "You look into the sky and find the moon softly staring back.\n\nYou're pretty sure it's a "

    if 0 < phase_angle < 7.4 or 352.6 <= phase_angle <= 360:
        return moon_response + "New Moon" + " right now."
    elif 7.4 <= phase_angle < 14.8:
        return moon_response + "First Quarter Waxing Crescent" + " right now."
    elif 14.8 <= phase_angle < 29.5:
        return moon_response + "Waxing Crescent" + " right now."
    elif 29.5 <= phase_angle < 44.8:
        return moon_response + "First Quarter Waxing Gibbous" + " right now."
    elif 44.8 <= phase_angle < 59.5:
        return moon_response + "Waxing Gibbous" + " right now."
    elif 59.5 <= phase_angle < 66.9:
        return moon_response + "Full Moon" + " right now."
    elif 66.9 <= phase_angle < 88.9:
        return moon_response + "Waning Gibbous" + " right now."
    elif 88.9 <= phase_angle < 96.3:
        return moon_response + "Last Quarter Waning Gibbous" + " right now."
    elif 96.3 <= phase_angle < 118.4:
        return moon_response + "Waning Crescent" + " right now."
    elif 118.4 <= phase_angle < 125.8:
        return moon_response + "New Moon" + " right now."
    else:
        return moon_response + "Unknown Moon Phase" + " right now."

def reset_action(session, user_input):
    session.clear()
    return("Session cleared.")


# Dictionary mapping user input to corresponding functions
action_dict = {
    'introspect': introspect_action,
    'status': status_action,
    'look': look_action,
    'where': where_action,
    'go': lambda session, user_input: go_action(session, user_input, user_input.split()[1] if len(user_input.split()) > 1 else ''),
    'help': help_action,
    'moon': moon_action,
    'reset': reset_action
}

def user_input_parser(user_input):
    action_function = action_dict.get(user_input.split()[0], lambda session, user_input: 'ERROR: Command not found')
    return action_function(session, user_input)

