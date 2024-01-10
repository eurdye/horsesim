from flask import Flask, session
import ephem

location_dict = {
        "0,0": "Summit Observatory",
        "0,1": "Devil's Tail",
        "1,1": "Temple of Fire",
        "1,2": "Monastery",
        "1,3": "Campgrounds",
        "1,6": "Hillside Caves",
        "1,7": "Unspoken Hills",
        "1,8": "Western Glassrock Cliffs",
        "1,9": "Mysterious Grotto",
        "2,0": "Hermitage",
        "2,1": "Lonesome Path",
        "2,3": "Bath House",
        "2,4": "Tea Cart",
        "2,7": "Unspoken Hills",
        "2,8": "Western Glassrock Cliffs",
        "3,3": "Upper Mountain Path",
        "3,4": "Lower Mountain Path",
        "3,8": "Western Beach",
        "4,4": "Mountain Train Station",
        "4,5": "Slime City Train Station",
        "4,8": "Beach",
        "5,3": "Slime City Uptown",
        "5,4": "Slime City Downtown",
        "5,5": "Slime City Transport Center",
        "5,6": "Slime City Bus Stop",
        "5,7": "Beach Bus Stop",
        "5,8": "Beach",
        "5,9": "Pier",
        "6,2": "Slime Commons",
        "6,3": "Peace of Pizza",
        "6,4": "Slime Park",
        "6,5": "Botanical Garden West",
        "6,8": "Awakening Beach",
        "7,2": "Your Apartment",
        "7,3": "Slime Apartments",
        "7,4": "Confectioner",
        "7,5": "Botanical Garden East",
        "7,8": "Eastern Glassrock Cliffs",
        "8,0": "Farm North",
        "8,1": "Farm South",
        "8,2": "Town Hall",
        "8,3": "General Store", 
        "8,4": "Casino",
        "8,5": "Club",
        "8,9": "Island"
    }

def where_action(session, user_input):
    global location_dict
    current_location = session.setdefault('location', {'x': 6, 'y': 8})
    current_key = f"{current_location['x']},{current_location['y']}"

    if current_key in location_dict:
        current_place = location_dict[current_key]
        adjacent_places = get_adjacent_places(current_location, location_dict)
        return f"You are at {current_place}. {adjacent_places}"
    else:
        return "You are in an unknown location."


def get_adjacent_places(current_location, location_dict):
    adjacent_places = []

    x = current_location['x']
    y = current_location['y']

    adjacent_coords = [
        (x, y + 1),  # North
        (x, y - 1),  # South
        (x + 1, y),  # East
        (x - 1, y),  # West
    ]

    for coord in adjacent_coords:
        key = f"{coord[0]},{coord[1]}"
        if key in location_dict:
            place_name = location_dict[key]
            direction = get_direction(current_location, coord)
            adjacent_places.append(f"To the {direction} is {place_name}.")

    return " ".join(adjacent_places)


def get_direction(current_location, adjacent_location):
    x_diff = adjacent_location[0] - current_location['x']
    y_diff = adjacent_location[1] - current_location['y']

    if x_diff == 0 and y_diff == 1:
        return "NORTH"
    elif x_diff == 0 and y_diff == -1:
        return "SOUTH"
    elif x_diff == 1 and y_diff == 0:
        return "EAST"
    elif x_diff == -1 and y_diff == 0:
        return "WEST"
    else:
        return "UNKNOWN"
# Show user's x, y coords when they type 'where'
def xy_action(session, user_input):
    return session.get('location', {})

# Function for navigating the world and moving around
def go_action(session, user_input, direction):
    current_location = session.setdefault('location', {'x': 6, 'y': 8})
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
        return "Where? Use \'go [north/south/east/west]\' to move in the specified direction."

    # Check if the new location is within valid bounds (0 to 9)
    if not (0 <= current_location['x'] <= 8 and 0 <= current_location['y'] <= 10):
        # If not within bounds, revert the move and return an error message
        session['location'] = prev_location
        return f"You can\'t go {direction.upper()} from here."

    global location_dict
    current_key = f"{current_location['x']},{current_location['y']}"

    if current_key not in location_dict:
        # If the new location is not in location_dict, revert the move and return an error message
        session['location'] = prev_location
        return f"You can\'t go {direction.upper()} from here."

    session['location'] = current_location
    if prev_location != current_location:
        return f'You head {direction.upper()}.\n\n' + where_action(session, user_input)
    else:
        return f'Already at {direction.upper()}.'

# Function to introspect, should check player's location and game progress then display the relevant message
def introspect_action(session, user_input):
    global location_dict
    current_location = session.setdefault('location', {'x': 6, 'y': 8})
    current_key = f"{current_location['x']},{current_location['y']}"
    game_progress = session.setdefault('game_progress', {'introspect': False})

    # Introspect to begin the game
    if current_key == "6,8" and game_progress["introspect"] == False:
        game_progress["introspect"] = True
        session['game_progress'] = game_progress
        return "Who are you? A fragile equine body lies heaped beneath you. You do not remember these muscles, this skin. You remember an argument. Fighting. A loss. Feelings, only vague, receding from you even now as your gaze drifts out over the endless sea... \n\nYou think you should take a LOOK around."
    elif current_key == "6,8":
        return "Test"

# Help command lists possible actions
def help_action(session, user_input):
    game_progress = session.setdefault('game_progress', {'introspect': False})
    action_list = list(action_dict.keys())
    print_actions = lambda keys: '\n'.join(keys)
        
    if game_progress['introspect'] == False:
        return "COMMAND LIST:\n" + print_actions(action_list) + "\n\nType 'introspect' and press enter to begin your adventure."
    else:
        return ("COMMAND LIST:\n" + print_actions(action_list))

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

def status_action(session, user_input):
    return session.get('game_progress', {})

def reset_action(session, user_input):
    session.clear()
    return("Session cleared.")

# Dictionary mapping user input to corresponding functions
action_dict = {
    'introspect': introspect_action,
    'location': where_action,
    'go': lambda session, user_input: go_action(session, user_input, user_input.split()[1] if len(user_input.split()) > 1 else ''),
    'moon': moon_action,
    'help': help_action,
    'status': status_action,
    'xy': xy_action,
    'reset': reset_action
}

def user_input_parser(user_input):
    action_function = action_dict.get(user_input.split()[0], lambda session, user_input: 'ERROR: Command not found')
    return action_function(session, user_input)

