from flask import Flask, session
import ephem
from datetime import datetime
import random
from john import john_responses
import eliza_action 
import csv
import uuid, os

# Instantiate ElizaBot
eliza_bot = eliza_action.ElizaBot()
monk_bot = eliza_action.MonkBot()
astrologer_bot = eliza_action.AstrologerBot()

# Function to generate a unique identifier for each user
def generate_unique_id():
    return str(uuid.uuid4())

# Function to save game progress to a CSV file
def save_game_progress(unique_id, game_progress):
    save_directory = "saves"
    filename = os.path.join(save_directory, f"{unique_id}_game_progress.csv")
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Assuming 'introspect', 'inventory', and 'feel' are keys in game_progress
        writer.writerow(['introspect', 'inventory', 'feel'])

        # Write data to the corresponding columns
        writer.writerow([game_progress.get('introspect', False), game_progress.get('inventory', {'apple': 0}), game_progress.get('feel', 'neutral')])

# Function to load game progress from a CSV file
def load_game_progress(unique_id):
    save_directory = "saves"
    filename = os.path.join(save_directory, f"{unique_id}_game_progress.csv")

    try:
        with open(filename, mode='r', newline='') as file:
            reader = csv.reader(file)
            keys = next(reader, None)  # Read the header row
            values = next(reader, None)  # Read the data row

            if keys is not None and values is not None:
                # Create a dictionary from keys and values
                game_progress = dict(zip(keys, values))

                # Ensure 'inventory' is a dictionary
                game_progress['inventory'] = eval(game_progress.get('inventory', '{}'))

                return game_progress
            else:
                # Return an empty dictionary if the file is empty
                return {}
    except FileNotFoundError:
        # Return an empty dictionary if the file is not found
        return {}

def load_location_from_csv(csv_filename):
    location_dict = {}
    with open(csv_filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            x = int(row['x'])
            y = int(row['y'])
            location_dict[f"{x},{y}"] = row['place']
    return location_dict

def where_action(session, user_input):
    # Load location_dict from CSV file
    location_dict = load_location_from_csv('locations.csv')

    current_location = session.setdefault('location', {'x': 6, 'y': 8})
    current_key = f"{current_location['x']},{current_location['y']}"

    if current_key in location_dict:
        current_place = location_dict[current_key]
        adjacent_places = get_adjacent_places(current_location)
        return f"You are at {current_place.upper()}. {adjacent_places}"
    else:
        return "You are in an unknown location."

def get_adjacent_places(current_location):
    location_dict = load_location_from_csv('locations.csv')
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
            place_name = place_name.upper()
            direction = get_direction(current_location, coord)
            adjacent_places.append(f"To the {direction} is {place_name}.")

    return " ".join(adjacent_places)


def get_direction(current_location, adjacent_location):
    x_diff = adjacent_location[0] - current_location['x']
    y_diff = adjacent_location[1] - current_location['y']

    if x_diff == 0 and y_diff == 1:
        return "SOUTH"
    elif x_diff == 0 and y_diff == -1:
        return "NORTH"
    elif x_diff == 1 and y_diff == 0:
        return "EAST"
    elif x_diff == -1 and y_diff == 0:
        return "WEST"
    else:
        return "UNKNOWN"

# Show user's x, y coords when they type 'xy'
def xy_action(session, user_input):
    return session.get('location', {})

# Function for navigating the world and moving around
def go_action(session, user_input, direction):
    # Load location_dict from CSV file
    location_dict = load_location_from_csv('locations.csv')

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
        current_location = session.setdefault('location', {'x': 6, 'y': 8})
        current_key = f"{current_location['x']},{current_location['y']}"
        if current_key in location_dict:
            adjacent_places = get_adjacent_places(current_location)
            return f"Where do you want to go? {adjacent_places}"

    # Check if the new location is within valid bounds (0 to 9)
    if not (0 <= current_location['x'] <= 8 and 0 <= current_location['y'] <= 10):
        # If not within bounds, revert the move and return an error message
        session['location'] = prev_location
        return f"You can\'t go {direction.upper()} from here."

    # Check if new location is available at the current time
    global current_time
    global earlymorning_start
    global morning_start
    global afternoon_start
    global evening_start
    global latenight_start
    observer = ephem.Observer()
    moon = ephem.Moon()

    # Set the observer's location (latitude and longitude)
    observer.lat = '34.135559'  # Replace with your latitude
    observer.lon = '-116.054169'  # Replace with your longitude

    # Compute the moon's phase
    moon.compute(observer)
    # Determine the moon phase
    phase_angle = moon.phase % 360

    # Mysterious Grotto only available in early morning
    if current_location['x'] == 1 and current_location['y'] == 9:
        if latenight_start >= current_time >= earlymorning_start:
            session['location'] = prev_location
            return "The tide is too high to access the MYSTERIOUS GROTTO."
    # Dream Temple only open during new and full moons
    if current_location['x'] == 1 and current_location['y'] == 2:
        if (7.4 <= phase_angle < 59.5) or (66.9 <= phase_angle <= 118.4):
            session['location'] = prev_location
            return "The DREAM TEMPLE is only open during lunar maxima."
    # Observatory only open at night
    if current_location['x'] == 0 and current_location['y'] == 0:
        if evening_start >= current_time >= morning_start:
            session['location'] = prev_location
            return "The OBSERVATORY is only open at night."

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
    # Load location_dict from CSV file
    location_dict = load_location_from_csv('locations.csv')

    current_location = session.setdefault('location', {'x': 6, 'y': 8})
    current_key = f"{current_location['x']},{current_location['y']}"

    # Check if UUID exists in the session, generate one if not
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())

    # Load game_progress from CSV file
    game_progress = load_game_progress(session.get('uuid', 'default_uuid'))

    # Introspect to begin the game
    if current_key == "6,8" and not game_progress.get("introspect", False):
        game_progress["introspect"] = True
        save_game_progress(session.get('uuid', 'default_uuid'), game_progress)       
        return "Who are you? A fragile equine body lies heaped beneath you. You do not remember these muscles, this skin. You remember an argument. Fighting. A loss. Feelings, only vague, receding from you even now as your gaze drifts out over the endless sea... \n\nYou think you should take a LOOK around."
    elif current_key == "6,8":
        return "Test"
    elif current_key == "0,0":
        return "The peak of the world... wherever this place is. Up here, above the clouds, the firmament above is so clear... You lift an equine eye to the heavens. If heaven is still up there, where does that put you? You try not to think about it.\n\nThe OBSERVATORY here has a powerful telescope. Maybe the ASTROLOGER will let you take a look. Maybe they know more about what this place is."

# Help command lists possible actions
def help_action(session, user_input):
    game_progress = session.setdefault('game_progress', {'introspect': False})
    action_list = list(action_dict.keys())
    print_actions = lambda keys: '\n'.join(keys)
        
    if game_progress['introspect'] == False:
        return "COMMAND LIST:\n" + print_actions(action_list) + "\n\nType 'introspect' and press enter to begin your adventure."
    else:
        #return ("COMMAND LIST:\n" + print_actions(action_list))
        return ("COMMAND LIST:\n introspect\ngo [north/south/east/west]\nwhere\nlook\ntalk [npc] [message]\nfeel [emotion]\nget [item]\nmoon\ntime\nhelp\nguide\n\nDEBUG:\nstatus\nxy\nwarp [x,y]\nreset")

# Guide command for more in depth game guide manual info
def guide_action(session, user_input):
    return("""Welcome to DEAD HORSE.\n
    DEAD HORSE is a real-time afterlife simulation game. Locations open and close, NPCs come and go, and topics of conversation vary based on the time of day and current moon phase.\n
    DEAD HORSE is an ambient game. There is no way to win or lose. All you can do is exist.\n
    The core gameplay of DEAD HORSE consists of exploring the world and talking to the various beings you will meet. Don't be afraid to get personal -- the folks in DEAD HORSE love to chat, whether that's helping you talk about your feelings or attempting to divine your future.\n
    When you meet someone you want to converse with, use the 'talk' command to talk with them. You can talk using natural language by typing 'talk [npc name] [your message]'.\n
    Example: 'talk monk hello, how are you?'""")

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

    moon_response = "You're pretty sure it's a "

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

# Global variables for time. Define time ranges and associated values.
current_time = datetime.now().time()
earlymorning_start = datetime.strptime('04:00:00', '%H:%M:%S').time()
morning_start = datetime.strptime('06:00:00', '%H:%M:%S').time()
afternoon_start = datetime.strptime('12:00:00', '%H:%M:%S').time()
evening_start = datetime.strptime('18:00:00', '%H:%M:%S').time()
latenight_start = datetime.strptime('22:00:00', '%H:%M:%S').time()

# Find current datetime
def time_action(session, user_input):
    global current_time
    global earlymorning_start
    global morning_start
    global afternoon_start
    global evening_start
    global latenight_start

    if current_time < earlymorning_start:
        return "It's late at night!"
    elif current_time < morning_start:
        return "It's early morning!"
    elif current_time < afternoon_start:
        return "It's morning!"
    elif current_time < evening_start:
        return "It's afternoon!"
    elif current_time < latenight_start:
        return "It's evening!"
    else:
        return "It's night time!"

def where_action_with_dynamic_value(session, user_input, location_dict, look_dict):
    current_location = session.setdefault('location', {'x': 6, 'y': 8})
    current_key = f"{current_location['x']},{current_location['y']}"

    if current_key in location_dict:
        current_place = location_dict[current_key]
        adjacent_places = get_adjacent_places(current_location)

        # Check if current_place is in look_dict
        if current_place in look_dict:
            dynamic_value = get_value_based_on_time()
            return f"You are at {current_place}. {adjacent_places}. Look: {look_dict[current_place]} ({dynamic_value})"
        else:
            return f"You are at {current_place}. {adjacent_places}. No additional information in look_dict."
    else:
        return "You are in an unknown location."

# Code for the 'look' command
# Put descriptions in look_dict
look_dict = {"Summit Observatory": 'At the top of the mountain, an OBSERVATORY. The half-dome houses a large TELESCOPE. Beneath you, clouds. Above, stars.',
             "Devil's Tail": '',
            "Hallowed Ground": '',
            "Dream Temple": 'A spacious yet plain space. You feel a tingly energy coarsing through you, as though you could bend the laws of reality but suddenly do not care to.',
            "Hidden Path": '',
            "Hillside Caves": '',
            "Unspoken Hills": '',
            "Western Glassrock Cliffs": '',
            "Mysterious Grotto": '',
            "Hermitage": '',
            "Lonesome Path": '',
            "Bath House": '',
            "Tea Cart": '',
            "Unspoken Hills": '',
            "Western Glassrock Cliffs": '',
            "Upper Mountain Path": '',
            "Lower Mountain Path": '',
            "Western Beach": '',
            "Mountain Train Station": '',
            "Slime City Train Station": '',
            "Western Beach": '',
            "Slime City Uptown": '',
            "Slime City Downtown": '',
            "Slime City Transport Center": '',
            "Slime City Bus Stop": '',
            "Beach Bus Stop": '',
            "Central Beach": 'The main stretch of beach, featuring a pier. There are some beings playing in the surf. It looks like this is where the bus lets everyone off, so most of the people who come to the beach stay around here.',
            "Pier": '',
            "Slime Commons": '',
            "Peace of Pizza": '',
            "Slime Park": '',
            "Botanical Garden": '',
            "Awakening Beach": 'A sandy beach upon which you awoke. The waves pound at the shore, throbbing in unison with your skull. The water stretches to the horizon. In the distance, you think you see an ISLAND. At your hooves, nothing but coarse sand.',
            "Your Apartment": '',
            "Slime Apartments": '',
            "Confectioner": '',
            "Therapist": '',
            "Eastern Glassrock Cliffs": '',
            "Farm North": '',
            "Farm South": '',
            "Town Hall": '',
            "General Store": '', 
            "Casino": '',
            "Club": '',
             "Island": ''
             }


def look_action(session, user_input):
    current_location = session.setdefault('location', {'x': 6, 'y': 8})
    current_key = f"{current_location['x']},{current_location['y']}"

    # Load location data from CSV
    location_dict = load_location_from_csv('locations.csv')

    global look_dict
    global npc_dict
    
    if current_key in location_dict:
        current_place = location_dict[current_key]
        adjacent_places = get_adjacent_places(current_location)

        # Check if current_place is in look_dict
        if current_place in look_dict:
            value_in_look_dict = look_dict[current_place]
            
            # Check if current_place is in npc_dict
            if npc_dict[current_place] == []:
                return f"You are at {current_place.upper()}. {value_in_look_dict}\n\n{adjacent_places}"
            elif npc_dict[current_place] is not []:
                available_npcs = npc_dict[current_place]
                available_npcs = [item.upper() for item in available_npcs]
                return f"You are at {current_place.upper()}. {value_in_look_dict}\n\nYou can TALK to {', '.join(available_npcs)}.\n\n{adjacent_places}"
        else:
            return f"You are at {current_place.upper()}.\n\n{adjacent_places}."
    else:
        return "You are in an unknown location."

import random

# Dictionary of available NPCs in each location
npc_dict = {
    "Summit Observatory": ['Astrologer'],
    "Devil's Tail": ['Pilgrim'],
    "Hallowed Ground": ['Angel'],
    "Dream Temple": ['Monk'],
    "Hidden Path": ['Deer Spirit'],
    "Hillside Caves": [],
    "Unspoken Hills": [],
    "Western Glassrock Cliffs": [],
    "Mysterious Grotto": ['Abyss'],
    "Hermitage": ['The Hermit'],
    "Lonesome Path": [],
    "Bath House": ['Attendant'],
    "Tea Cart": ['Tea Lady'],
    "Unspoken Hills": [],
    "Western Glassrock Cliffs": [],
    "Upper Mountain Path": [],
    "Lower Mountain Path": [],
    "Western Beach": [],
    "Mountain Train Station": ['Conductor'],
    "Slime City Train Station": ['Conductor'],
    "Western Beach": [],
    "Slime City Uptown": [],
    "Slime City Downtown": [],
    "Slime City Transport Center": [],
    "Slime City Bus Stop": ['Bus Driver'],
    "Beach Bus Stop": ['Bus Driver'],
    "Central Beach": [],
    "Pier": [],
    "Slime Commons": [],
    "Peace of Pizza": ['Pizza Girl'],
    "Slime Park": [],
    "Botanical Garden": [],
    "Awakening Beach": ['John'],
    "Your Apartment": [],
    "Slime Apartments": [],
    "Confectioner": ['The Confectioner'],
    "Therapist": ['Eliza'],
    "Eastern Glassrock Cliffs": [],
    "Farm North": ['Farm Wife'],
    "Farm South": ['Farm Wife'],
    "Town Hall": ['Princess'],
    "General Store": ['Trader'], 
    "Casino": ['Gambler'],
    "Club": ['Raver'],
    "Island": ['Castaway']
}

# Function for talking to NPCs
def talk_action(session, user_input):
    current_location = session.setdefault('location', {'x': 6, 'y': 8})
    current_key = f"{current_location['x']},{current_location['y']}"

    global npc_dict
    location_dict = load_location_from_csv('locations.csv')

    if current_key in location_dict:
        current_place = location_dict[current_key]
        adjacent_places = get_adjacent_places(current_location)

        # Check if current_place is in npc_dict
        if current_place in npc_dict:
            available_npcs = npc_dict[current_place]
            current_place = current_place.upper()
            # Check if user specified an NPC
            if len(user_input.split()) > 1:
                npc_name = user_input.split()[1].capitalize()

                if npc_name in available_npcs:
                    if npc_name == 'John':
                        # Check for full moon and add comment
                        moon_phase = get_moon_phase(session, user_input)
                        if 0<= moon_phase <= 5:
                            greeting = "\""+random.choice(john_responses['new_moon_comment'])+"\""
                            return greeting
                        else:
                            greeting = "\""+random.choice(john_responses['greeting'])+"\""
                            return greeting
                    elif npc_name == 'Eliza':
                        # Sanitize user_input if it begins with "talk eliza "
                        prefix = "talk eliza "
                        if user_input.lower().startswith(prefix):
                            user_input = user_input[len(prefix):].strip()
                        eliza_response = eliza_bot.respond(user_input)
                        return eliza_response
                    elif npc_name == 'Monk':
                        # Sanitize user_input if it begins with "talk monk "
                        prefix = "talk monk "
                        if user_input.lower().startswith(prefix):
                            user_input = user_input[len(prefix):].strip()
                        monk_response = monk_bot.respond(user_input)
                        return monk_response
                    elif npc_name == 'Astrologer':
                        # Sanitize user_input if it begins with "talk astrologer "
                        prefix = "talk astrologer "
                        if user_input.lower().startswith(prefix):
                            user_input = user_input[len(prefix):].strip()
                        astrologer_response = astrologer_bot.respond(user_input)
                        return astrologer_response
                    else:
                        available_npcs = [item.upper() for item in available_npcs]
                        return f"No specific responses defined for {npc_name}."
                else:
                    available_npcs = [item.upper() for item in available_npcs]
                    return f"{npc_name} is not here. You can talk to the following at {current_place}: {', '.join(available_npcs)}"
            else:
                available_npcs = [item.upper() for item in available_npcs]
                return f"You can talk to the following at {current_place}: \n\n{', '.join(available_npcs)}"
        else:
            return f"No one available to talk to at {current_place}"
    else:
        return "You are in an unknown location."

def status_action(session, user_input):
    # Get the player's current emotion from the session
    player_emotion = session.get('emotion', 'neutral')

    # Check if the user input is "status"
    if user_input.strip().lower() == "status":
        return f"You are feeling {player_emotion}."
    else:
        return "Unknown command."

def reset_action(session, user_input):
    session.clear()
    return("Session cleared.")

# Function to get the moon phase
def get_moon_phase(session, user_input):
    today = ephem.now()
    moon = ephem.Moon(today)
    phase_name = moon.phase
    return phase_name

# Global variable to store player inventory
# 0 = obtainable, 1 = in inventory, 2 = taken out of inventory, 3 = unobtainable
#player_inventory = session.setdefault('inventory', {'apple': 0})

# Function to handle "get" action
def get_action(session, user_input):
    # Check if UUID exists in the session, generate one if not
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())
    # Load game_progress from CSV file
    game_progress = load_game_progress(session.get('uuid', 'default_uuid'))

    # Get or initialize the player's inventory from the session
    player_inventory = game_progress.setdefault('inventory', {'apple': 0})

    # Check if the user input contains "get"
    if "get" in user_input:
        # Extract the item name after "get"
        item_name = user_input.split("get", 1)[-1].strip().lower()

        # Check if the item name is valid
        if item_name:
            # Check the value of the item in the player's inventory
            item_status = player_inventory.get(item_name)
            if item_status is None:
                # Item not in dictionary
                return f"{item_name} not found."
            if item_status == 0:
                # Item is obtainable, add it to the inventory
                player_inventory[item_name] = 1
                game_progress['inventory'] = player_inventory
                save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
                return f"You obtained {item_name}."
            elif item_status == 1:
                # Item is already in the inventory
                return f"You already have {item_name} in your inventory."
            elif item_status == 2:
                # Item was given to NPC
                return f"You no longer have {item_name}."
            else:
                # Item is unobtainable
                return f"{item_name} is unobtainable."
        else:
            return "Please specify an item to get."
    else:
        return "You can use the 'get' command to obtain items."

# Function to handle "emote" action
def emote_action(session, user_input):
    # Get or initialize the player's emotion from the session
    player_emotion = session.setdefault('emotion', 'neutral')

    # List of possible emotions
    possible_emotions = ['joy', 'sadness', 'anger', 'surprise', 'fear', 'neutral', 'mirth']

    # Extract the emotion name after "feel"
    emotion_name = user_input.split("feel", 1)[-1].strip().lower()

    # Check if the emotion name is valid
    if emotion_name:
        # Check if the emotion is in the list of possible emotions
        if emotion_name in possible_emotions:
            # Check if the player is already feeling the same emotion
            if emotion_name == player_emotion:
                return f"You are already feeling {emotion_name.upper()}."
            else:
                # Update the player's emotion in the session
                session['emotion'] = emotion_name
                
                # Load game_progress from CSV file
                game_progress = load_game_progress(session.get('uuid', 'default_uuid'))
                
                # Save the updated emotion information in the 'feel' column
                game_progress['feel'] = emotion_name
                save_game_progress(session.get('uuid', 'default_uuid'), game_progress)

                return f"You are now feeling {emotion_name.upper()}."
        else:
            return f"You don't know how to feel {emotion_name.upper()}."
    else:
        return "What do you want to feel?"

def warp_action(session, user_input, location):
    # Extract X and Y coordinates from the input
    try:
        x, y = map(int, location.split(','))
    except ValueError:
        return "Invalid warp coordinates. Please use 'warp X,Y' format."

    # Check if the new location is within valid bounds (0 to 8 for X, 0 to 10 for Y)
    if not (0 <= x <= 8 and 0 <= y <= 10):
        return "Invalid warp coordinates. Coordinates must be within the valid bounds."

    # Update the user's location
    session['location'] = {'x': x, 'y': y}

    # Return a message indicating the successful warp
    return f"You have warped to {x},{y}."


# Dictionary mapping user input to corresponding functions
action_dict = {
    'introspect': introspect_action,
    'look': look_action,
    'where': where_action,
    'go': lambda session, user_input: go_action(session, user_input, user_input.split()[1] if len(user_input.split()) > 1 else ''),
    'get': get_action,
    'moon': moon_action,
    'feel': emote_action,
    'talk': talk_action,
    'time': time_action,
    'help': help_action,
    'guide': guide_action,
    'status': status_action,
    'xy': xy_action,
    'warp': lambda session, user_input: warp_action(session, user_input, user_input.split()[1] if len(user_input.split()) > 1 else ''),
    'reset': reset_action
}

def user_input_parser(user_input):
    action_function = action_dict.get(user_input.split()[0], lambda session, user_input: 'ERROR: Command not found')
    return action_function(session, user_input)

