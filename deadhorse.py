from flask import Flask, session
import ephem
from datetime import datetime
import random
import csv
import uuid, os

# Function to generate a unique identifier for each user
def generate_unique_id():
    return str(uuid.uuid4())

# Function to save game progress to a CSV file
def save_game_progress(unique_id, game_progress):
    save_directory = "saves"
    # Ensure the 'saves' directory exists
    os.makedirs(save_directory, exist_ok=True)
    filename = os.path.join(save_directory, f"{unique_id}_game_progress.csv")
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Assuming 'introspect', 'inventory', and 'feel' are keys in game_progress
        writer.writerow(['introspect', 'inventory', 'feel'])

        # Write data to the corresponding columns
        writer.writerow([game_progress.get('introspect', 0), game_progress.get('inventory', {'apple': 0, 'pillow': 0}), game_progress.get('feel', 'neutral')])

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
        return f"You are at {current_place.upper()}.\n\n{adjacent_places}"
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

    # Sunken Grotto only available in early morning
    if current_location['x'] == 1 and current_location['y'] == 9:
        if latenight_start >= current_time >= morning_start:
            session['location'] = prev_location
            return "The tide is too high to access the SUNKEN GROTTO. Maybe in the early morning..."
    # Dream Temple only open during new and full moons
    if current_location['x'] == 1 and current_location['y'] == 2:
        if (7.4 <= phase_angle < 59.5) or (66.9 <= phase_angle <= 118.4):
            session['location'] = prev_location
            return "The DREAM TEMPLE is only open during full and new moons."
    # Observatory only open at night
    if current_location['x'] == 0 and current_location['y'] == 0:
        if evening_start >= current_time >= earlymorning_start:
            session['location'] = prev_location
            return "The OBSERVATORY is only open at night."
    if current_location['x'] == 4 and (current_location['y'] == 5 or current_location['y'] == 4):
        if (evening_start <= current_time) and (current_time >= morning_start):
            session['location'] = prev_location
            return "The TRAIN STATION is closed at night."
    if current_location['x'] == 5 and (current_location['y'] == 6 or current_location['y'] == 7):
        if (evening_start <= current_time) and (current_time >= morning_start):
            session['location'] = prev_location
            return "The BUS STOP is closed at night."

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
    introspect_progress = int(game_progress['introspect'])

    # Introspect to begin the game
    if (current_key == "6,8") and (introspect_progress == 0):
        game_progress["introspect"] = '1'
        save_game_progress(session.get('uuid', 'default_uuid'), game_progress)       
        return "Who are you? A fragile equine body lies heaped beneath you. You do not remember these muscles, this skin. You remember an argument. Fighting. A loss. Feelings, only vague, receding from you even now as your gaze drifts out over the endless sea... \n\nYou think you should take a LOOK around."
    elif current_key == "6,8" and (10011 > introspect_progress > 0):
        if introspect_progress == 1:
            game_progress["introspect"] = (int(game_progress["introspect"]) + 10)
            save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
        return "This is where you found yourself when you awoke in this strange reality... And yet your first thoughts were of yourself. Your identity. What does that mean? What does that say about the sort of being you are?"
    elif current_key == "1,9":
        if introspect_progress < 100:
            game_progress["introspect"] = (int(game_progress["introspect"]) + 100)
            save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
        return "You gaze into the Abyss below. Something inside of you swells. Is that the remnant of your soul? Forced into this purgatory, this rough shape. Yes, you are certain you are being punished. What are you guilty of?"
    elif current_key == "1,1":
        if introspect_progress < 1000:
            game_progress["introspect"] = (int(game_progress["introspect"]) + 1000)
            save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
        return "You find it hard to turn within here... a force pulls you into space, keeps your awareness on the material. What is it that makes you want to burst so? As though your insides long to come gushing out... You feel as though nothing can remain hidden in this space. As though the atoms would sooner rend apart than obstruct. A space of ultimate clarity. And yet here is where you are most opaque. What does this mean?"
    elif current_key == "0,0":
        if introspect_progress < 10000:
            game_progress["introspect"] = (int(game_progress["introspect"]) + 10000)
            save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
        return "The peak of the world... wherever this place is. Up here, above the clouds, the firmament above is so clear... You lift an equine eye to the heavens. If heaven is still up there, where does that put you? You try not to think about it.\n\nThe OBSERVATORY here has a powerful telescope. Maybe the ASTROLOGER will let you take a look. Maybe they know more about what this place is."
    elif current_key == "6,5" and (100 > introspect_progress > 10):
        if introspect_progress < 100:
            game_progress["introspect"] = (int(game_progress["introspect"]) + 100)
            save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
        return "You sit among the gardens, wondering how you found yourself here. Before the ocean, you remember nothing. Were you born or made? How did you come to be? What could possibly have given birth to you? (Another horse? You dare not think it.)"
    elif current_key == "6,5" and (introspect_progress > 100):
        return "Among the plants, you wonder if you are much different. A horse among God's garden. Growing desperately toward the sun. You do not know what forces have incarnated you here, but you imagine they may stop by sometime to water roots and prune branches."
    elif current_key == "6,8" and (introspect_progress > 10000):
        if introspect_progress > 10000:
            game_progress["introspect"] = (int(game_progress["introspect"]) + 100000)
            save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
        return "You reflect on your travels, and what you've learned about yourself in turn. The beings you've met. The strange places you've been. You still feel no closer to any answers. Yet somehow you feel you know yourself a little better. These hooves don't seem so unfamiliar. This skin feels like it belongs. Perhaps this equine form is no punishment at all, but a chance to start again."
    elif current_key == "5,8":
        return "You get kind of self-conscious with the MERMAID over there. You feel so awkward in your ungulate form. You bet she could tell some more about this world, though, or give some tips to help you survive. You've heard that MERMAIDS only talk to beings who FEEL JOY. You better FEEL JOY before you go talk to her, or she'll just give you the silent treatment." 
    else:
        return "You don't think you can INTROSPECT right now."

# Help command lists possible actions
def help_action(session, user_input):
    action_list = list(action_dict.keys())
    print_actions = lambda keys: '\n'.join(keys)
        
    #return ("COMMAND LIST:\n" + print_actions(action_list))
    return ("""COMMAND LIST:
            'go [north/south/east/west]' - navigate the world
            'talk [npc] [message]' - talk to npc
            'feel [emotion]' - feel emotions
            'get [item]' - obtain items
            'introspect' - reflect on your journey
            'look' - describes the area you are in
            'look [item]' - describes item in your inventory
            'what' - shows your inventory
            'where' - shows where you are
            'when' - check the time and moon
            'help' - shows command list
            'guide' - shows game manual

            DEBUG:
            status - shows game_progress var
            xy - shows current xy coords
            warp [x,y] - warp to xy coords
            reset - starts a new save""")

# Guide command for more in depth game guide manual info
def guide_action(session, user_input):
    return("""Welcome to DEAD HORSE.\n
    DEAD HORSE is a real-time (after)life simulation game. Locations open and close, NPCs come and go, and topics of conversation vary based on the time of day and current moon phase.\n
    DEAD HORSE is an ambient game. It cannot be beaten and there is no way to lose. After all, you're already dead.\n
    The core gameplay of DEAD HORSE consists of exploring the world and talking to the various beings you will meet. When you meet someone you want to converse with, use the 'talk' command to talk with them. You can talk using natural language by typing a command like this:\n\n'talk [npc name] [your message]\n
    Some beings will converse with you if you bring up the right topic or if you're in the right mood.\n
    Introspection is another key part of the gameplay. Depending on your location and frame of mind, introspecting can lead to inner growth, unlocking new emotions and allowing you to go deeper within.""")


# Global variables for time. Define time ranges and associated values.
current_time = datetime.now().time()
earlymorning_start = datetime.strptime('04:00:00', '%H:%M:%S').time()
morning_start = datetime.strptime('06:00:00', '%H:%M:%S').time()
afternoon_start = datetime.strptime('12:00:00', '%H:%M:%S').time()
evening_start = datetime.strptime('18:00:00', '%H:%M:%S').time()
latenight_start = datetime.strptime('22:00:00', '%H:%M:%S').time()

# Find current datetime and moon phase
def time_action(session, user_input):
    global current_time
    global earlymorning_start
    global morning_start
    global afternoon_start
    global evening_start
    global latenight_start

    # Find current moon phase
    observer = ephem.Observer()
    moon = ephem.Moon()

    # Set the observer's location (latitude and longitude)
    observer.lat = '34.135559'  # Replace with your latitude
    observer.lon = '-116.054169'  # Replace with your longitude

    # Compute the moon's phase
    moon.compute(observer)
    # Determine the moon phase
    phase_angle = moon.phase % 360

    moon_response = "Looks like it's a "

    if 0 < phase_angle < 7.4 or 352.6 <= phase_angle <= 360:
        moon_response = moon_response + "NEW" + " MOON right now."
    elif 7.4 <= phase_angle < 14.8:
        moon_respons = moon_response + "FIRST QUARTER WAXING CRESCENT" + " MOON right now."
    elif 14.8 <= phase_angle < 29.5:
        moon_response = moon_response + "WAXING CRESCENT" + " MOON right now."
    elif 29.5 <= phase_angle < 44.8:
        moon_response = moon_response + "FIRST QUARTER WAXING GIBBOUS" + " MOON right now."
    elif 44.8 <= phase_angle < 59.5:
        moon_response =  moon_response + "WAXING GIBBOUS" + " MOON right now."
    elif 59.5 <= phase_angle < 66.9:
        moon_response = moon_response + "FULL" + " MOON right now."
    elif 66.9 <= phase_angle < 88.9:
        moon_response = moon_response + "WANING GIBBOUS" + " MOON right now."
    elif 88.9 <= phase_angle < 96.3:
        moon_response = moon_response + "LAST QUARTER WANING GIBBOUS" + " MOON right now."
    elif 96.3 <= phase_angle < 118.4:
        moon_response = moon_response + "WANING CRESCENT" + " MOON right now."
    elif 118.4 <= phase_angle < 125.8:
        moon_response = moon_response + "NEW" + " MOON right now."
    else:
        moon_response = moon_response + "UNKNOWN MOON PHASE" + " MOON right now."

    if current_time < earlymorning_start:
        time_response = "It's currently LATE NIGHT."
    elif current_time < morning_start:
        time_response = "It's currently EARLY MORNING."
    elif current_time < afternoon_start:
        time_response = "It's currently MORNING."
    elif current_time < evening_start:
        time_response = "It's currently AFTERNOON."
    elif current_time < latenight_start:
        time_response = "It's currently EVENING."
    else:
        time_response = "It's currently NIGHT."

    return time_response + "\n\n" + moon_response

def where_action_with_dynamic_value(session, user_input, location_dict, look_dict):
    current_location = session.setdefault('location', {'x': 6, 'y': 8})
    current_key = f"{current_location['x']},{current_location['y']}"

    if current_key in location_dict:
        current_place = location_dict[current_key]
        adjacent_places = get_adjacent_places(current_location)

        # Check if current_place is in look_dict
        if current_place in look_dict:
            dynamic_value = get_value_based_on_time()
            return f"You are at {current_place}.\n\n{adjacent_places}. Look: {look_dict[current_place]} ({dynamic_value})"
        else:
            return f"You are at {current_place}.\n\n{adjacent_places}. No additional information in look_dict."
    else:
        return "You are in an unknown location."

# Code for the 'look' command
# Put descriptions in look_dict
look_dict = {"Summit Observatory": 'At the top of the mountain, a half-dome houses a large TELESCOPE. Beneath you, clouds. Above, stars.',
             "Devil's Tail": 'A precarious trail up to the top of the world. Careful--it\'s narrow. Your hooves quiver. The air sure is thin up here.',
             "Hallowed Ground": 'Even death has grounds it respects. This area is hallowed. You aren\'t quite sure what that means, but you believe it. Every hair on your equine torso stands on end. You are in the presence of... something...',
             "Dream Temple": 'A spacious yet plain space. You feel a tingly energy coarsing through you, as though you could bend the laws of reality but suddenly do not care to. The monks here each have a PILLOW on which they sit.',
             "Hidden Path": 'A small hidden path further up the mountain. Only the most dedicated seekers uncover this trail.',
             "Hillside Caves": 'There are a number of caves along the hillside here. Where do they lead?',
             "Unspoken Hills": 'The Unspoken Hills are unspeakable.',
             "Western Glassrock Cliffs": 'The sharp rock of the beach digs into your hooves, discovering where they are still soft. Beneath you, the ocean churns.',
             "Sunken Grotto": 'A half-sunked cavern. Watery shadows dance on the walls. During high tide, the whole cave floods. At low tide each night it becomes accessible on hoof for a few hours. You feel an eerie presence here, as though you are witnessing something you\'re not supposed to. You feel on edge. Darkness pervades as you peer into the ABYSS.',
             "Hermitage": 'The most solitary place in the whole afterlife. Is someone home?',
             "Lonesome Path": 'A lonely path further up the mountain. You fear you are getting lost.',
             "Bath House": 'Ah, a refreshing bath house. Take a hot bath and sit in the sauna. Let your equine muscles release. Restore sheen to your mane. Unblock your energies.',
             "Tea Cart": 'Green tea, black tea, oolong... you can\'t decide!',
             "Unspoken Hills": 'You dare not speak of them.',
             "Western Glassrock Cliffs": 'The sharp rock of the beach digs into your hooves, discovering where they are still soft. Beneath you, the ocean churns.',
             "Upper Mountain Path": 'This path leads further up the mountain.',
             "Lower Mountain Path": 'This is the path at the base of the mountain.',
             "Chiron's Cove": 'The beach on the west side. Sandy.',
             "Mountain Train Station": 'There are few travelers here. The train station lets you off at the base of the mountain, a short walk to the village to the WEST.',
             "Slime City Train Station": 'The train station in SLIME CITY. Boy, you wonder where all these beings came from and where they are going. Are they all dead, too? Death is full of mysteries.',
             "Western Shore": 'The broad expanse of the WESTERN SHORE stretches on. There is a lot of sand and water.',
             "Slime City Uptown": 'Uptown Slime City, baby! Money, fame, and plenty of fortune, too. Ah--who are you kidding--it\'s empty here, too.',
             "Slime City Downtown": 'Slime City Downtown, baby! Hustle, bustle, and plenty of old-school funk.',
             "Slime City Transport Center": 'The transport center. Trains and buses stop here from all over, bringing souls to SLIME CITY.',
             "Slime City Bus Stop": 'The bus to the BEACH departs from here.',
             "Beach Bus Stop": 'The bus to the BEACH departs from here.',
             "Central Shoreline": 'The main stretch of beach, featuring a pier. The purple waters of the ENDLESS OCEAN lap rhythmically at the shore. A number of beings appear to have gathered here to observe the waters. Down by the water, A MERMAID lounges in the sand. She looks like she could give you some important information.',
             "Pier": 'The wood groans beneath you, begging to give way. Waves pound at the ancient structure. Your hooves echo with each step. A cold ocean spray chills your tail. In the waters below, a DOLPHIN taunts your land-stricken body by swimming and giggling enthusiastically.',
             "Slime Commons": 'Everybody hangs out here!',
             "Peace of Pizza": 'Your favorite restaurant ever.',
             "Slime Park": 'The park. You have a sudden urge to eat grass.',
             "Botanical Garden": 'Tall agave, cacti, sage, various trees, grasses, flowers... you see an APPLE fall from a tree.',
             "Odd Beach": 'A sandy beach upon which you awoke. The waves pound at the shore, throbbing in unison with your skull. The water stretches to the horizon. In the distance, you think you see an ISLAND. At your hooves, nothing but coarse sand.',
             "Your Apartment": 'You live here?',
             "Slime Apartments": 'Other people live here',
             "Confectioner": 'Do horses have sweet tooths? You\'re not sure. Do you want to find out? You\'re also not sure.',
             "Therapist": 'You know, you could probably use some therapy, being dead and all.',
             "Eastern Glassrock Cliffs": 'Yeeowch.',
             "Farm North": 'This is where they grow food.',
             "Farm South": 'This is where they keep the farm animals. No horses, hopefully.',
             "Town Hall": 'The seat of the local government, you guess. Who\'s really in charge here, anyway?',
             "General Store": 'Buy, sell, trade. Your three favorite things.', 
             "Casino": 'Gambling is legal in the afterlife. Not that you have any money to gamble with.',
             "Club": 'What else is there to do when you\'re dead but dance the night away?',
             "Island": 'Woah. Is this one of those dessert islands? No. It\'s made of sand. It\'s one of those stupid desert islands instead.'
             }

item_desc_dict = {
        "apple": "A delicious-looking apple. Seriously, now that you're a horse, it's really hard to resist eating it. Still, you decide to put it in your... pocket?... for later.",
        'pillow': "A plain round pillow. You're not sure how you're supposed to sit on it, being a horse and all. Still, you figure it might come in handy. And it was so nice of that monk to give it to you. He seemed to truly take pity on your current state."
        }

def look_action(session, user_input):
    current_location = session.setdefault('location', {'x': 6, 'y': 8})
    current_key = f"{current_location['x']},{current_location['y']}"

    # Load location data from CSV
    location_dict = load_location_from_csv('locations.csv')

    global look_dict
    global npc_dict
    global item_desc_dict

    # Check if UUID exists in the session, generate one if not
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())
    # Load game_progress from CSV file
    game_progress = load_game_progress(session.get('uuid', 'default_uuid'))

    # Get or initialize the player's inventory from the session
    player_inventory = game_progress.setdefault('inventory', {'apple': 0, 'pillow': 0})

    # Load location_dict from CSV file
    location_dict = load_location_from_csv('locations.csv')

    current_location = session.setdefault('location', {'x': 6, 'y': 8})
    current_key = f"{current_location['x']},{current_location['y']}"

    if current_key in location_dict:
        current_place = location_dict[current_key]

    # Check if the user input contains "look" and an item
    if user_input.startswith("look "):
        item_to_look = user_input.split(" ", 1)[1]  # Extract the item from the user input

        # Check if the item is in the user's inventory
        if item_to_look in player_inventory.keys():
            # Replace this with the actual description retrieval logic for items
            item_description = item_desc_dict.get(item_to_look, f"Description for {item_to_look}.")
            return item_description
        else:
            return f"You don't have {item_to_look} in your inventory."
    
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
                return f"You are at {current_place.upper()}. {value_in_look_dict}\n\nYou can TALK to {', '.join(available_npcs)}."
        else:
            return f"You are at {current_place.upper()}."
    else:
        return "You are in an unknown location."

import random

# Dictionary of available NPCs in each location
npc_dict = {
    "Summit Observatory": ['Astrologer'],
    "Devil's Tail": [],
    "Hallowed Ground": [],
    "Dream Temple": ['Monk'],
    "Hidden Path": ['Deer'],
    "Hillside Caves": [],
    "Unspoken Hills": [],
    "Western Glassrock Cliffs": [],
    "Sunken Grotto": ["Abyss"],
    "Hermitage": ["Hermit"],
    "Lonesome Path": [],
    "Bath House": ["Stranger"],
    "Tea Cart": ["Lady"],
    "Unspoken Hills": [],
    "Western Glassrock Cliffs": [],
    "Upper Mountain Path": [],
    "Lower Mountain Path": [],
    "Chiron's Cove": [],
    "Mountain Train Station": ["Conductor"],
    "Slime City Train Station": ["Conductor"],
    "Western Shore": [],
    "Slime City Uptown": [],
    "Slime City Downtown": [],
    "Slime City Transport Center": [],
    "Slime City Bus Stop": ["Driver"],
    "Beach Bus Stop": ["Driver"],
    "Central Shoreline": ["Mermaid"],
    "Pier": ["Dolphin"],
    "Slime Commons": [],
    "Peace of Pizza": ["Girl"],
    "Slime Park": [],
    "Botanical Garden": [],
    "Odd Beach": [],
    "Your Apartment": [],
    "Slime Apartments": [],
    "Confectioner": [],
    "Therapist": ['Eliza'],
    "Eastern Glassrock Cliffs": [],
    "Farm North": [],
    "Farm South": [],
    "Town Hall": ["Princess"],
    "General Store": [], 
    "Casino": [],
    "Club": [],
    "Island": []
}

# Create a dictionary to store the chatbot instances
npc_bots = {}

# Iterate through the dictionary and dynamically create classes and instances
for location, npcs in npc_dict.items():
    for npc in npcs:
        # Define a new class dynamically
        class_name = f"{npc}Bot"
        class_definition = f"""
import npc_bot

class {class_name}:
    def __init__(self):
        self.eliza_instance = npc_bot.eliza.Eliza()
        self.eliza_instance.load('npcs/{npc.lower()}.txt')

    def respond(self, user_input):
        return self.eliza_instance.respond(user_input)
"""

        # Create the class dynamically using exec
        exec(class_definition)

        # Instantiate the dynamically created class
        bot_instance = locals()[class_name]()
        
        # Store the bot instance in the dictionary
        npc_bots[npc] = bot_instance


# Function for talking to NPCs
def talk_action(session, user_input):
    current_location = session.setdefault('location', {'x': 6, 'y': 8})
    current_key = f"{current_location['x']},{current_location['y']}"
    # Check if UUID exists in the session, generate one if not
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())
    # Load game_progress from CSV file
    game_progress = load_game_progress(session.get('uuid', 'default_uuid'))
    save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
    game_progress = load_game_progress(session.get('uuid', 'default_uuid'))

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
    
    global npc_dict
    location_dict = load_location_from_csv('locations.csv')

    if current_key in location_dict:
        current_place = location_dict[current_key]
        adjacent_places = get_adjacent_places(current_location)

        # Check if current_place is in npc_dict
        if current_place in npc_dict:
            available_npcs = npc_dict[current_place]
            current_place = current_place.upper()

            if available_npcs == []:
                return f"There is no one available to talk to at {current_place}"

            # Check if user specified an NPC
            if len(user_input.split()) > 1:
                npc_name = user_input.split()[1].capitalize()

                if npc_name in available_npcs:
                    if npc_name in npc_bots:  # Check if the NPC has a corresponding chatbot instance
                        if npc_name == 'Mermaid' and game_progress['feel'] != 'joy':
                            return f'The {npc_name} refuses to speak with you. Your vibes must be off!'
                        elif npc_name == 'Dolphin' and game_progress['feel'] != 'mirth':
                            return f'The {npc_name} refuses to speak with you. Your vibes must be off!'
                        elif npc_name == 'Hermit' and game_progress['feel'] != 'calm':
                            return f'The {npc_name} refuses to speak with you. Your vibes must be off!'
                        elif npc_name == 'Abyss' and game_progress['feel'] != 'divine terror':
                            return f'You\'re not in the right state of mind to commune with the ABYSS. Come back when you\'re experiencing DIVINE TERROR.'
                       
                        # Sanitize user_input if it begins with "talk {npc_name.lower()} "
                        prefix = f"talk {npc_name.lower()} "
                        if user_input.lower().startswith(prefix):
                            user_input = user_input[len(prefix):].strip()

                        if npc_name.lower() == "mermaid" and (evening_start >= current_time < morning_start):
                            return "MERMAID has returned to the sea for the night"
                        elif npc_name.lower() == "astrologer" and (morning_start <= current_time < evening_start):
                            return "The ASTROLOGER is unavailable during the day."
                        elif npc_name.lower() == 'deer' and (96.3 <= phase_angle < 118.4):
                            return "The DEER spirit ignores you."
                        elif npc_name.lower() == 'stranger' and ((0 < phase_angle < 1) or (19 < phase_angle < 20) or (42 < phase_angle < 45) or (66.7 < phase_angle < 72)):
                            return "The STRANGER is not here today."
     
                        # Get the chatbot instance from the dictionary
                        bot_instance = npc_bots[npc_name]
 
                        # Use the chatbot instance to respond
                        npc_response = bot_instance.respond(user_input)
                        return npc_response
                    else:
                        return f"No chatbot instance found for {npc_name}."
                else:
                    available_npcs = [item.upper() for item in available_npcs]
                    return f"{npc_name} is not here. You can talk to the following at {current_place}: {', '.join(available_npcs)}"
            else:
                available_npcs = [item.upper() for item in available_npcs]
                return f"You can talk to the following at {current_place}:\n\n{', '.join(available_npcs)}"
        else:
            return f"No one available to talk to at {current_place}"
    else:
        return "You are in an unknown location."

def status_action(session, user_input):
    game_progress = load_game_progress(session.get('uuid', 'default_uuid'))
    return game_progress

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

# Function to handle "get" action
def get_action(session, user_input):
    # Check if UUID exists in the session, generate one if not
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())
    # Load game_progress from CSV file
    game_progress = load_game_progress(session.get('uuid', 'default_uuid'))

    # Get or initialize the player's inventory from the session
    player_inventory = game_progress.setdefault('inventory', {'apple': 0, 'pillow': 0})

    # Load location_dict from CSV file
    location_dict = load_location_from_csv('locations.csv')

    current_location = session.setdefault('location', {'x': 6, 'y': 8})
    current_key = f"{current_location['x']},{current_location['y']}"

    if current_key in location_dict:
        current_place = location_dict[current_key]

    # 0 = obtainable, 1 = in inventory, 2 = taken out of inventory, 3 = unobtainable
    if player_inventory['apple'] != 1:
        if current_place == "Botanical Garden":
            player_inventory['apple'] = 0
        else:
            player_inventory['apple'] = 3

    if player_inventory['pillow'] != 1:
        if current_place == 'Dream Temple':
            player_inventory['pillow'] = 0
        else:
            player_inventory['pillow'] = 3  

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
    # Check if UUID exists in the session, generate one if not
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())
    # Load game_progress from CSV file
    game_progress = load_game_progress(session.get('uuid', 'default_uuid'))
    save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
    game_progress = load_game_progress(session.get('uuid', 'default_uuid'))
    player_emotion = game_progress['feel']

    # List of possible emotions
    possible_emotions = ['joy', 'sadness', 'anger', 'fear', 'divine terror', 'neutral', 'mirth', 'calm']

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
                # Save the updated emotion information in the 'feel' column
                game_progress['feel'] = emotion_name
                save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
                return f"You are now feeling {emotion_name.upper()}."
        else:
            return f"You don't know how to FEEL {emotion_name.upper()}."
    else:
        return f"You are currently feeling {player_emotion.upper()}."

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

# Function to display inventory
def what_action(session, user_input):
    # Check if UUID exists in the session, generate one if not
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())
    # Load game_progress from CSV file
    game_progress = load_game_progress(session.get('uuid', 'default_uuid'))

    # Get or initialize the player's inventory from the session
    player_inventory = game_progress.setdefault('inventory', {'apple': 0, 'pillow': 0})
    player_inventory = [key for key, value in player_inventory.items() if value == 1]
    if player_inventory == []:
        return "You have nothing in your inventory."
    else:
        player_inventory = '\n(1) '.join(key.upper() for key in player_inventory)
        player_inventory = "INVENTORY:\n(1) " + player_inventory
        return player_inventory
 
# Dictionary mapping user input to corresponding functions
action_dict = {
    'introspect': introspect_action,
    'look': look_action,
    'where': where_action,
    'go': lambda session, user_input: go_action(session, user_input, user_input.split()[1] if len(user_input.split()) > 1 else ''),
    'get': get_action,
    'feel': emote_action,
    'talk': talk_action,
    'when': time_action,
    'what': what_action,
    'help': help_action,
    'guide': guide_action,
    'status': status_action,
    'xy': xy_action,
    'warp': lambda session, user_input: warp_action(session, user_input, user_input.split()[1] if len(user_input.split()) > 1 else ''),
    'reset': reset_action
}

def user_input_parser(user_input):

    # Check if UUID exists in the session, generate one if not
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())
    # Load game_progress from CSV file
    game_progress = load_game_progress(session.get('uuid', 'default_uuid'))
    save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
    game_progress = load_game_progress(session.get('uuid', 'default_uuid'))

    # Split user input into words
    input_words = user_input.split()

    # Check if there are any words in the input
    if not input_words:
        return 'ERROR: No command entered'

    action_function = action_dict.get(user_input.split()[0], lambda session, user_input: 'ERROR: Command not found')
   
    if (user_input.lower() != 'introspect' and user_input.lower() != 'help' and user_input.lower() != 'guide' and user_input.lower() != 'status') and int(game_progress['introspect']) == 0:
        return "Type 'introspect' and press enter to begin your journey."
    else:
        return action_function(session, user_input)

