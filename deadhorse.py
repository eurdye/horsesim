from flask import Flask, session, jsonify
import ephem
from datetime import datetime
import pytz
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
        writer.writerow([game_progress.get('introspect', 0), game_progress.get('inventory', {'apple': 0, 'towel': 0, 'tea': 0, 'mirror': 0, 'book': 0, 'pizza': 0, 'pillow': 0}), game_progress.get('feel', 'neutral')])

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

    current_location = session.setdefault('location', {'x': 7, 'y': 8})
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

    current_location = session.setdefault('location', {'x': 7, 'y': 8})
    prev_location = dict(current_location)  # Store previous location for comparison

    if direction == 'north':
        current_location['y'] -= 1
    elif direction == 'south':
        current_location['y'] += 1
    elif direction == 'east':
        current_location['x'] += 1
    elif direction == 'west':
        current_location['x'] -= 1
    elif direction == 'island' or direction == 'pier':
        #current_location['x'] = 9
        #current_location['y'] = 9
        useless_var = 0 # need something here or it won't run
    else:
        current_location = session.setdefault('location', {'x': 7, 'y': 8})
        current_key = f"{current_location['x']},{current_location['y']}"
        if current_key in location_dict:
            adjacent_places = get_adjacent_places(current_location)
            return f"Go where?\n\n{adjacent_places}"

    # Check if the new location is within valid bounds (0 to 9)
    if not (0 <= current_location['x'] <= 9 and 0 <= current_location['y'] <= 9):
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
    phase_angle = moon.phase

    # Sunken Grotto only available in early morning
    if current_location['x'] == 2 and current_location['y'] == 9:
        if latenight_start >= current_time >= morning_start:
            session['location'] = prev_location
            return "The tide is too high to access the SUNKEN GROTTO. Try coming back late at night."
    # Dream Temple only open during new and full moons
    if current_location['x'] == 1 and current_location['y'] == 2:
        if (phase_angle > 5):
            if (phase_angle < 95):
                session['location'] = prev_location
                return "The DREAM TEMPLE is only open during the new and full moon."
    # Observatory only open at night
    if current_location['x'] == 0 and current_location['y'] == 0:
        if evening_start >= current_time >= earlymorning_start:
            session['location'] = prev_location
            return "The OBSERVATORY is only open at night. Try coming back in the evening."
    # Train Station and Bus Stop closed at night
    if (current_location['x'] == 4 or current_location['x'] == 5) and (current_location['y'] == 5):
        if (evening_start <= current_time) and (current_time >= morning_start):
            session['location'] = prev_location
            return "The TRAIN STATION is closed at night. Try coming back in the morning."
    if current_location['x'] == 6 and (current_location['y'] == 6 or current_location['y'] == 7):
        if (evening_start <= current_time) and (current_time >= morning_start):
            session['location'] = prev_location
            return "The BUS STOP is closed at night. Try coming back in the morning."
    # Island only open during days during new moon
    if current_location['x'] == 6 and current_location['y'] == 9 and direction == 'island':
        if (latenight_start <= current_time) and (current_time >= morning_start):
            session['location'] = prev_location
            return "You cannot visit the ISLAND at night. Return once the sun is up."
        else:
            warp_action(session, "warp", "9,9")
            return "You row the boat to the ISLAND."
    if current_location['x'] == 9 and current_location['y'] == 9 and direction == 'pier':
        warp_action(session, "warp", "6,9")
        return "You row the boat back to the PIER."

    # Change feeling at certain locations
    '''
    if current_location['x'] == 5 and (current_location['y'] == 8):
        emote_action(session, "feel sonder")
    '''

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

    current_location = session.setdefault('location', {'x': 7, 'y': 8})
    current_key = f"{current_location['x']},{current_location['y']}"

    # Check if UUID exists in the session, generate one if not
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())

    # Load game_progress from CSV file
    game_progress = load_game_progress(session.get('uuid', 'default_uuid'))
    introspect_progress = int(game_progress['introspect'])

    if (current_key == "0,0") and (introspect_progress > 0):
        if introspect_progress < 10000:
            game_progress["introspect"] = (int(game_progress["introspect"]) + 10000)
            save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
        return "The peak of the world... wherever this place is. Up here, above the clouds, the firmament above is so clear... You lift an equine eye to the heavens. If heaven is still up there, where does that put you? You try not to think about it.\n\nThe OBSERVATORY here has a powerful telescope. Maybe the ASTROLOGER will let you take a look. Maybe they know more about what this place is."
    elif (current_key == "0,1") and (introspect_progress > 0):
        return "You wonder why they call it the DEVIL'S TAIL. Who even is the DEVIL anyway? Is he real? What's his deal? You find it kind of hard to imagine a being made of pure evil. Maybe it is just a reference to an old myth or local legend."
    elif (current_key == "1,1") and (introspect_progress > 0):
        if introspect_progress < 1000:
            game_progress["introspect"] = (int(game_progress["introspect"]) + 1000)
            save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
        return "You find it hard to turn within here... a force pulls you into space, keeps your awareness on the material. What is it that makes you want to burst so? As though your insides long to come gushing out... You feel as though nothing can remain hidden in this space. As though the atoms would sooner rend apart than obstruct. A space of ultimate clarity. And yet here is where you are most opaque. What does this mean?"
    elif (current_key == "1,2"):
        return "The DREAM TEMPLE make you reflect on your dreams recently. Now that you think of it, what have your dreams been recently? You woke up here... and now you're a horse... have you even had time to dream? Perhaps the journey here has been one long dream. Perhaps the MONK could chat about where you've been, or the dreamlike nature of REALITY. Then again, you're not sure you want to know the truth, if the truth exists..."
    elif (current_key == "1,3"):
        emote_action(session, "feel vexed")
        return "The small HIDDEN PATH leaves you FEELING strangely VEXED. You're not sure why, but you think your presence here is unappreciated. You feel as though you should hurry along lest you disturb something better left alone."
    elif (current_key == "2,0"):
        emote_action(session, "feel calm")
        return "You clear your mind and go inwards. You FEEL perfectly CALM. There is no voice that responds, no thoughts that arise, nothing. You are your body and your body is the world."
    elif (current_key == "2,1"):
        return "Walking the LONESOME PATH, your mind turns to your relationships. Who have you met thus far in your journey? What conversations have you had? Have you been a good horse and kind to other beings? Who has helped you and who have you helped? What have you taken and what have you given? You realize you are not so alone."
    elif (current_key == "2,3"):
        return "While in the BATH HOUSE, you think about your body, the way it aches and shivers, the coldness of your hooves and the softness of your mane. You think about the way it feels unhomely, like something not meant to exist. You think about the existence of the BATH HOUSE as a shrine dedicated to bodies -- to caring for bodies and giving them love. You think that is pretty cool."
    elif (current_key == "2,4"):
        player_inventory = game_progress.setdefault('inventory', {'apple': 0, 'towel': 0, 'tea': 0, 'mirror': 0, 'book': 0, 'pizza': 0, 'pillow': 0})
        if player_inventory['tea'] == 0:
            return "You find it hard to concentrate on anything without a cup of TEA. You think you should go GET some before INTROSPECTING here."
        elif player_inventory['tea'] == 1:
            player_inventory['tea'] = 2
            save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
            emote_action(session, "feel jouissance")
            return "You sip your TEA and think about times you were happy. You wonder if you will ever feel that way again. Here, sipping your tea, you FEEL a JOUISSANCE overcome you as you reach a state of pure contentment. You aren't sure if you feel happy, but you feel grateful to exist, grateful for the fact of being.\n\nYum, what a good tea!"
        else:
            return "You think about that cup of TEA and remember how content you felt to hold it, the JOUISSANCE you experienced while drinking it."
    elif (current_key == "2,6"):
        emote_action(session, "feel divine terror")
        return "You sit within the mouth of a cave and ponder your current state of existence. Here you are, a horse, sitting in a cave. You let out a whinny, listening to it echo back. The sound feels at once unfamiliar and intimate. You feel the presence of something else beside you. Your body feels weak. You FEEL DIVINE TERROR. Something horrible must have happened here."
        # The view here is nice. You wonder if there could be peace in death."
    elif (current_key == "2,7") or (current_key == "3,7"):
        return "As you climb through the UNSPOKEN HILLS, you find yourself reflecting on the struggles in your life. You can't remember much, though, so you mostly think about how hard it was to walk this far. You think about your life as an uphill struggle. You feel as though you are constantly climbing up cliffs. Perhaps being a horse who is dead is the latest one."
    elif (current_key == "2,8") or (current_key == "3,8"):
        return "The WESTERN GLASSROCK CLIFFS are a little gentler than you had anticipated. You find your thoughts turning to your tendency to overestimate obstacles. Are you holding yourself back? Are you inventing things to be afraid of? You remember being afraid of death... somewhere in your mind, you are certain of it... yet, here you are. A horse. Dead. And, somehow, you are still doing things."
    elif (current_key == "2,9"):
        if introspect_progress < 100:
            game_progress["introspect"] = (int(game_progress["introspect"]) + 100)
            save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
        return "You gaze into the Abyss below. Something inside of you swells. Is that the remnant of your soul? Forced into this purgatory, this rough shape. Yes, you are certain you are being punished. What are you guilty of?"
    elif (current_key == "3,4") or (current_key == "4,4"):
        return "You tread the MOUNTAIN PATH, wondering where it will take you. What could be awaiting you, wherever you are going? Why do you go where you go? What compels you to move, to do anything at all? You wonder all these questions, but never come to any satisfying conclusion."
    elif (current_key == "4,5") or (current_key == "5,5"):
        emote_action(session, "feel joy")
        return "You gain a FEELING of JOY from riding and being around trains. You wonder why this is. You wonder why you are not satisfied with your own locomotive ability. You wonder if you could ever be satisfied with the capabilities of your own body. Especially since you're a horse."
    elif (current_key == "4,8"):
        return "CHIRON gives you a sense of unease. You get the feeling you should not linger too long here. You wonder if there was ever any chance of things being different."
    elif (current_key == "5,8"):
        return """As you walk along the sand, your mind wanders, lulled by the soft rumble of the waves. You look back at the hoofprints in the sand. Markers of where you've been. Here you have a presence. Here you leave traces of your past. You cannot say the same for wherever it is you came from. The ocean left no evidence of where you had been before. You wonder if that may be a blessing."""
    elif (current_key == "6,2"):
        return "You nestle into a small nook in the corner of the LIBRARY and find your thoughts drifting within. Here you are--a strange library in a stranger town. Yet most strange of all: you still do not know yourself. Who are you? Your thoughts return to the first words that came into your equine mind. You do not have an answer."
    elif (current_key == "6,3"):
        return "SLIME CITY UPTOWN looks like it's the 'good neighborhood.' Why does the afterlife still have good and bad parts of town? What even is an UPTOWN, anyway? You are a simple horse. You are not sure you ever knew the answer to that question. Yet, here you are, in an UPTOWN. Even without knowing what it is, it still shapes your being."
    elif (current_key == "6,4"):
        emote_action(session, "feel sonder")
        return "You know, you'd think it would be hard to introspect in a crowded city like this, but you find yourself feeling more alone than ever. You walk down the streets gazing at the beings passing you by, all strangers, all wandering souls. You have nothing more than this fleeting connection with them before they're gone forever. And yet you can't help but feel that you are the same and the whole city is one large super-being that you are all small pieces of. The busy streets give you a FEELING of SONDER."
    elif (current_key == "6,5"):
        return "At the TRANSPORT CENTER, you find your mind in a tizzy from the large amounts of information, as well as the crowds of beings traveling to and fro. You focus on getting to your destination--wherever that is--and choose not to introspect further at this time."
    elif (current_key == "6,6") or (current_key == "6,7"):
        return "Standing at the bus station, you find yourself thinking about how you relate to yourself and others based on your ability to travel. You wonder what wonders await you in either SLIME CITY or the BEACH. You wonder if you will succeed, or if you will continue to fail. You don't know why, but you feel like becoming a horse was a failure of some sort. A reflection of personal shortcoming. You wonder if there is anything you can do to change."
    elif (current_key == "6,8"):
        return "You get kind of self-conscious with the MERMAID over there. You feel so awkward in your ungulate form. You bet she could tell some more about this world, though, or give some tips to help you survive. You've heard that MERMAIDS only talk to beings who FEEL JOY. You better FEEL JOY before you go talk to her, or she'll just give you the silent treatment." 
    elif (current_key == "6,9"):
        emote_action(session, "feel mirth")
        return "You try to turn your focus inward, but that DOLPHIN keeps you on edge. It is so full of MIRTH that you find your mind FEELING oppressively MIRTHFUL in turn."
    elif (current_key == "7,2"):
        emote_action(session, "feel joy")
        return "The COMMONS makes you FEEL JOY. Beings are playing and having fun. Good conversations and good times, by the looks of things. You wonder if you could ever experience that for yourself. Still, being here helps you feel a little more cheerful."
    elif (current_key == "7,3"):
        return "You find your thoughts overwhelmingly turn to PIZZA. It's like that GIRL has psychic powers or something. PIZZA! You don't even know why you just thought that. Is she speaking to you? PIZZA! Is she listening? You PIZZA until you PIZZA but PIZZA PIZZA PIZZA PIZZA PIZZA!"
    elif (current_key == "7,4"):
        return "The park is nice enough. That feeling to eat grass is really strong, though. You wonder if they ever play music in the park. You're not sure why, but you feel like you would enjoy some live music in this location."
    elif (current_key == "7,5") and (100 > introspect_progress > 10):
        if introspect_progress < 100:
            game_progress["introspect"] = (int(game_progress["introspect"]) + 100)
            save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
        return "You sit among the gardens, wondering how you found yourself here. Before the ocean, you remember nothing. Were you born or made? How did you come to be? What could possibly have given birth to you? (Another horse? You dare not think it.)"
    elif (current_key == "7,5") and (introspect_progress >= 100):
        return "Among the plants, you wonder if you are much different. A horse among God's garden. Growing desperately toward the sun. You do not know what forces have incarnated you here, but you imagine they may stop by sometime to water roots and prune branches."
    # Introspect to begin the game
    elif (current_key == "7,8") and (introspect_progress == 0):
        game_progress["introspect"] = '1'
        save_game_progress(session.get('uuid', 'default_uuid'), game_progress)       
        return "Who are you? A fragile equine body lies heaped beneath you. You do not remember these muscles, this skin. You remember an argument. Fighting. A loss. Feelings, only vague, receding from you even now as your gaze drifts out over the endless ocean... \n\nYou think you should take a LOOK around."
    elif (current_key == "7,8") and (10011 > introspect_progress > 0):
        if introspect_progress == 1:
            game_progress["introspect"] = (int(game_progress["introspect"]) + 10)
            save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
        return "This is where you found yourself when you awoke in this strange reality... And yet your first thoughts were of yourself. Your identity. What does that mean? What does that say about the sort of being you are?"
    elif (current_key == "7,8") and (introspect_progress > 10000):
        game_progress["introspect"] = (int(game_progress["introspect"]) + 100000)
        save_game_progress(session.get('uuid', 'default_uuid'), game_progress)
        return "You reflect on your travels, and what you've learned about yourself in turn. The beings you've met. The strange places you've been. You still feel no closer to any answers. Yet somehow you feel you know yourself a little better. These hooves don't seem so unfamiliar. This skin feels like it belongs. Perhaps this equine form is no punishment at all, but a chance to start again."
    elif (current_key == "8,2"):
        return "This is your apartment, yet you don't feel at home. You don't remember ever being here before in your life. Or in your death. So why is it still yours? Did something happen here? Or... was that a memory? You catch the smell of... someone familiar... but it vanishes before you can recall any more."
    elif (current_key == "8,3"):
        emote_action(session, "feel sonder")
        return "Walking past the rows of APARTMENTS makes you FEEL SONDER. You wonder how many of the beings that live here you will get to meet. You wonder if any of the beings you've already met live here. You wonder who built the apartments, and who maintains them, and how property law works here. You find it all a bit much for your equine mind."
    elif (current_key == "8,4"):
        return "The CONFECTIONER does not make you feel safe. You find yourself wondering how to get out of here."
    elif (current_key == "8,5"):
        emote_action(session, "feel calm")
        return "Being at the THERAPIST'S office brings you a strange FEELING of CALM. It's like all your problems disappeared because you walked in here. What were you even upset about?"
    elif (current_key == "8,8"):
        emote_action(session, "feel petulance")
        return "You find yourself FEELING PETULANCE as you scale the cliffs. The glassrock digs into your hooves. You tell yourself you deserve it, but you know you do not. You wonder why you decided to go this way. You think about how much better you would be feeling if you were on the BEACH right now." 
    elif (current_key == "9,1"):
        emote_action(session, "feel vexed")
        return "The FARM. Is this where you belong now? Should you stay here forever? Are all animals just people who are dead? You don't know the answers to any of these questions. But they leave you FEELING quite VEXED."
    elif (current_key == "9,2"):
        return "Government stresses you out. The TOWN HALL seems chill enough, but the PRINCESS is a little strange. You think it is generally a good idea to avoid politicians and hope they don't notice you."
    elif (current_key == "9,3"):
        return "You wonder if there is anything you could want to buy or sell in the afterlife. You don't have any money. You wonder if it's possible to get money in the afterlife. You wonder why money still exists when everyone is dead."
    elif (current_key == "9,4"):
        return "You think about whether gambling is ethical or not, and find yourself wondering what sort of arrangement the CASINO has with the local government. Maybe you will stop by TOWN HALL later on to ask. You feel like the CASINO could be ethical, but it probably isn't. You're not really sure what sort of money they even have in this strange world, or the sorts of CASINO games people play. Also, it smells like smoke in here, and you find it irritating your equine nostrils."
    elif (current_key == "9,5"):
        emote_action(session, "feel ecstasy")
        return "You take some time to INTROSPECT at the CLUB. CLUB 7 OF CLUBS is chill with it. The loud beats and thumping bass give you something that FEELS like ECSTASY. You feel like all your problems are melting away, disappeared, unimportant. Who cares you're a horse anyway? You're here to dance! And you're feeling the music! You find yourself losing all inhibitions. You feel dangerous yet relieved."
    elif (current_key == "9,9"):
        return "You finally made it to the ISLAND. You thought you would be more excited. You feel like you should be more excited. Why aren't you excited? Did you hype yourself up too much? Is it your own fault you're not enjoying this as much as you could be, as much as you expected to? Are you the reason you're sad and dead and a horse?"
    else:
        return "You do not feel like you can INTROSPECT here. You decide to journey further."

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
            'reset' - resets your game
            'clear' - clears the screen""")
'''
            DEBUG:
            status - shows game_progress var
            xy - shows current xy coords
            warp [x,y] - warp to xy coords
            reset - starts a new save""")
'''

# Guide command for more in depth game guide manual info
def guide_action(session, user_input):
    return("""Welcome to DEAD HORSE.\n
    DEAD HORSE is a real-time afterlife simulation game. Locations open and close and beings come and go based on the time of day and current moon phase.\n
    DEAD HORSE is an ambient game. It cannot be beaten and there is no way to lose. After all, you're already dead.\n
    The core gameplay of DEAD HORSE consists of exploring the world and talking to the various beings you will meet. When you meet someone you want to converse with, use the 'talk' command to talk with them. You can talk using natural language by typing a command like this:\n\n'talk [npc name] [your message]'\n
    Some beings will only converse with you if you bring up the right topic or if you're in the right mood.\n""")


# Global variables for time. Define time ranges and associated values.
earlymorning_start = datetime.strptime('04:00:00', '%H:%M:%S').time()
morning_start = datetime.strptime('06:00:00', '%H:%M:%S').time()
afternoon_start = datetime.strptime('12:00:00', '%H:%M:%S').time()
evening_start = datetime.strptime('18:00:00', '%H:%M:%S').time()
latenight_start = datetime.strptime('22:00:00', '%H:%M:%S').time()

# Set the time zone to 'America/Los_Angeles'
desired_timezone = pytz.timezone('America/Los_Angeles')
current_time = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(desired_timezone).time()
#current_time = datetime.now().time()

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
    phase_angle = moon.phase

    if (0 <= phase_angle <= 5):
        moon_response = "It's a NEW MOON right now."
    elif 5 < phase_angle <= 20:
        moon_response = "The MOON is LESS THAN ONE QUARTER FULL right now."
    elif 20 < phase_angle <= 30:
        moon_response = "The MOON is about ONE QUARTER FULL right now."
    elif 30 < phase_angle <= 45:
        moon_response = "The MOON is A BIT LESS THAN HALF FULL right now."
    elif 45 < phase_angle < 55:
        moon_response = "The MOON is HALF FULL right now."
    elif 55 <= phase_angle < 70:
        moon_response = "The MOON is A BIT MORE THAN HALF FULL right now."
    elif 70 <= phase_angle < 80:
        moon_response = "The MOON is about THREE QUARTERS FULL right now."
    elif 80 <= phase_angle < 95:
        moon_response = "The MOON is MORE THAN THREE QUARTERS FULL right now."
    elif 95 <= phase_angle <= 100:
        moon_response = "It's a FULL MOON right now."
    else:
        moon_response = moon_response + "UNKNOWN MOON PHASE" + " MOON right now."

    if current_time < earlymorning_start:
        return current_time
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
    current_location = session.setdefault('location', {'x': 7, 'y': 8})
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
             "Dream Temple": 'A spacious yet plain space. It feels very intentional, as though every inch of space here was the result of intense concentration and rigorous knowledge. You feel a tingly energy rushing through you, as though you could bend the laws of reality but suddenly do not care to. The monks here each have a PILLOW on which they sit.',
             "Hidden Path": "A small hidden path further up the mountain. Only the most dedicated seekers uncover this trail. It is overgrown with vegetation. Doesn't look like it gets traveled much, if ever, these days.",
             "Hillside Caves": "There are a number of caves along the hillside here. Where do they lead? You don't think you want to go into one. You feel like you would get stuck, still unsure of the particulars of your equine form. You decide to stay near the surface, grateful for the shelter the cave mouths bring.",
             "Unspoken Hills": 'The Unspoken Hills are unspeakable. You cannot find the words to describe them. A hush falls upon you as you walk. Even your hoofsteps sound dampened.',
             "Western Glassrock Cliffs": 'The sharp rock of the beach digs into your hooves, discovering where they are still soft. Beneath you, the ocean churns.',
             "Sunken Grotto": 'A half-sunked cavern. Watery shadows dance on the walls. During high tide, the whole cave floods. At low tide each night it becomes accessible on hoof for a few hours. You feel an eerie presence here, as though you are witnessing something you\'re not supposed to. You feel on edge. Darkness pervades as you peer into the ABYSS.',
             "Hermitage": 'The most solitary place in the whole afterlife. Is someone home?',
             "Lonesome Path": 'A lonely path further up the mountain. You fear you are getting lost.',
             "Bath House": 'Ah, a refreshing bath house. Take a hot bath and sit in the sauna. Let your equine muscles release. Restore sheen to your mane. Unblock your energies. Gather strength for your journey.',
             "Tea Cart": 'Green tea, black tea, oolong... you can\'t decide!',
             "Unspoken Hills": 'You dare not speak of them.',
             "Western Glassrock Cliffs": 'The sharp rock of the beach digs into your hooves, discovering where they are still soft. Beneath you, the ocean churns.',
             "Upper Mountain Path": 'This path leads further up the mountain.',
             "Lower Mountain Path": 'This is the path at the base of the mountain.',
             "Chiron's Cove": "This COVE is quite nice. In the shadow of the WESTERN GLASSROCK CLIFFS, it gives you a feeling of security and ease. The water here is quiet and calm. CHIRON seems to be here an awful lot, but he keeps mostly to himself.",
             "Mountain Train Station": 'There are few travelers here. The train station lets you off at the base of the mountain, a short walk to the village to the WEST.',
             "Slime City Train Station": 'The train station in SLIME CITY. Boy, you wonder where all these beings came from and where they are going. Are they all dead, too? Death is full of mysteries.',
             "Western Shore": "This is the boring part of the beach. There's nothing here but just a bunch of sand.",
             "Library": 'Wow, look at all these books. You aren\'t sure if you know how to read. The architecture is nice, though. Hmm--what\'s that? Maybe there is a BOOK you can read.',
             "Slime City Uptown": 'It\'s UPTOWN SLIME CITY, baby! Money, fame, and plenty of fortune, too. Ah--who are you kidding--it\'s empty here, too.',
             "Slime City Downtown": 'It\'s SLIME CITY DOWNTOWN, baby! Hustle, bustle, and plenty of old-school funk.',
             "Slime City Transport Center": 'Trains and buses stop here from all over, bringing souls to SLIME CITY.',
             "Slime City Bus Stop": 'The bus to the BEACH departs from here.',
             "Beach Bus Stop": 'The bus to the BEACH departs from here.',
             "Central Shoreline": 'The main stretch of beach, featuring a pier. The purple waters of the ENDLESS OCEAN lap rhythmically at the shore. A number of beings appear to have gathered here to observe the waters. Down by the water, A MERMAID lounges in the sand. She looks like she could give you some important information.',
             "Pier": 'The wood groans beneath you, begging to give way. Waves pound at the ancient structure. Your hooves echo with each step. A cold ocean spray chills your tail. In the waters below, a DOLPHIN taunts your land-stricken body by swimming and giggling enthusiastically.',
             "Slime Commons": 'Everybody hangs out here!',
             "Peace-a-Pizza": "A restaurant themed around pizza and peace. You suppose the two go together if you don't think about it too hard. The GIRL who works here seems really enthusiastic about pizza. Maybe you should GET a slice... you are kind of hungry. Horses can eat pizza, right?",
             "Slime Park": 'The park in the middle of SLIME CITY. You have a sudden urge to eat grass, but you are worried they may use some extra-deadly afterlife pesticides here that would wreak havoc on your equine digestive system.',
             "Botanical Garden": 'Tall agave, cacti, sage, various trees, grasses, and flowers line the walkways. This garden is meticulously tended and hideously well cared for. The lush foliage and rich variety imparts you a strange FEELING of GUILT. You see an APPLE fall from a tree.',
             "Odd Beach": 'A sandy beach upon which you awoke. The waves pound at the shore, throbbing in unison with your skull. The water stretches to the horizon. At your hooves, nothing but coarse sand.',
             "Your Apartment": "You don't totally understand, but you guess you live here now. Your stuff is here? Not that you really have anything. It looks like a normal, plain apartment. There's a fridge and a sink, though you're not sure what good they'll do you now. There's a MIRROR here, too...",
             "Slime Apartments": 'Tall rows of apartments line the streets. Other beings live here.',
             "Confectioner": 'Rows of multicolored candy lines the shelves. A haunting jingle plays continuously on a music box. There is a smell so sweet it seems dangerous. Do horses like sugar? You\'re not sure. Do you want to find out? You\'re also not sure.',
             "Therapist": 'You know, you could probably use some therapy, being dead and all. You seem like you have a lot of problems and stuff to work through. This building seems nice enough, and the therapist ELIZA has some good reviews.',
             "Eastern Glassrock Cliffs": 'The CLIFFS rise incredibly high. The rock is unbelievably sharp. You can only walk a little ways in before it gets to be too much.',
             "Farm South": 'This is where they keep the farm animals. No horses, as far as you can see. You wonder about the other farm animals. They also have some crop fields.',
             "Town Hall": 'The seat of the local government, you guess. Who\'s really in charge here, anyway?',
             "General Store": 'Buy, sell, trade. Your three favorite things.', 
             "Casino": 'Gambling is legal in the afterlife. Not that you have any money to gamble with.',
             "Club 7 of Clubs": "What else is there to do when you\'re dead but dance the night away? CLUB 7 OF CLUBS is the hottest club in the afterlife, with banging tunes dropping 24/7. Stop by any time, any day for a party you'll never forget.",
             "Island": "A ruined pillar sits in the center of the ISLAND, indicating that something greater one stood here. Inscribed on the base of the pillar is the symbol for mercury. There is some stone and a small patch of grass nearby. You feel a spray of water against your flank. The air smells strongly of salt."
             }

# Item descriptions for if the user types 'look [item]'
item_desc_dict = {
        "apple": "A delicious-looking APPLE. Seriously, now that you're a horse, it's really hard to resist eating it. Still, you decide to put it in your... pocket?... for later.",
        "book": "This BOOK is about... well... you'll get around to reading it soon. The librarian gave it her highest recommendation. And just look at that cover! You're sure this will be a real page-turner, even if you did get it from the philosophy section.",
        "mirror": "A small handheld MIRROR that reflects your equine form. A reminder of your past sins.",
        'tea': "A cup of TEA freshly brewed.",
        'towel': "A nice fluffy towel from the BATH HOUSE. This thing is super absorbent!",
        'pillow': "A plain round PILLOW. You're not sure how you're supposed to sit on it, being a horse and all. Still, you figure it might come in handy. And it was so nice of that monk to give it to you. He seemed to truly take pity on your current state.",
        'pizza': "A delicious slice of piping-hot fresh-out-the-oven PIZZA!"
        }

def look_action(session, user_input):
    current_location = session.setdefault('location', {'x': 7, 'y': 8})
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
    player_inventory = game_progress.setdefault('inventory', {'apple': 0, 'towel': 0, 'tea': 0, 'mirror': 0, 'book': 0, 'pizza': 0, 'pillow': 0})

    # Load location_dict from CSV file
    location_dict = load_location_from_csv('locations.csv')

    current_location = session.setdefault('location', {'x': 7, 'y': 8})
    current_key = f"{current_location['x']},{current_location['y']}"

    if current_key in location_dict:
        current_place = location_dict[current_key]

    # Check if the user input contains "look" and an item
    if user_input.startswith("look "):
        item_to_look = user_input.split(" ", 1)[1]  # Extract the item from the user input

        # Check if the item is in the user's inventory
        if item_to_look in player_inventory.keys() and player_inventory[item_to_look] == 1:
            # Replace this with the actual description retrieval logic for items
            item_description = item_desc_dict.get(item_to_look, f"Description for {item_to_look}.")
            return item_description
        elif item_to_look in player_inventory.keys() and player_inventory[item_to_look] != 1:
            return f"You don't have {item_to_look.upper()} in your inventory."
        else:
            return f"ERROR: Invalid item."
    
    if current_key in location_dict:
        current_place = location_dict[current_key]
        adjacent_places = get_adjacent_places(current_location)

        # Check if current_place is in look_dict
        if current_place in look_dict:
            value_in_look_dict = look_dict[current_place]
            if current_place == "Island":
                return f"You are at {current_place.upper()}. {value_in_look_dict}\n\nTo return to the PIER, type 'go pier'."


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
    "Chiron's Cove": ["Chiron"],
    "Mountain Train Station": ["Conductor"],
    "Slime City Train Station": ["Conductor"],
    "Western Shore": [],
    "Library": ["Librarian"],
    "Slime City Uptown": [],
    "Slime City Downtown": [],
    "Slime City Transport Center": [],
    "Slime City Bus Stop": ["Driver"],
    "Beach Bus Stop": ["Driver"],
    "Central Shoreline": ["Mermaid"],
    "Pier": ["Dolphin"],
    "Slime Commons": [],
    "Peace-a-Pizza": ["Girl"],
    "Slime Park": [],
    "Botanical Garden": [],
    "Odd Beach": [],
    "Your Apartment": ["Reflection"],
    "Slime Apartments": [],
    "Confectioner": [],
    "Therapist": ['Eliza'],
    "Eastern Glassrock Cliffs": [],
    "Farm South": [],
    "Town Hall": ["Princess"],
    "General Store": [], 
    "Casino": [],
    "Club 7 of Clubs": [],
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
    current_location = session.setdefault('location', {'x': 7, 'y': 8})
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
    phase_angle = moon.phase
    
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
                            return f'The {npc_name} refuses to speak with you. It doesn\'t respect your attitude enough to converse!'
                        elif npc_name == 'Monk' and game_progress['feel'] != 'calm':
                            return f'The {npc_name} refuses to speak with you. You have a wild aura about you that disturbs the dream-fields. Maybe if you FELT more CALM...'
                        elif npc_name == 'Hermit' and game_progress['feel'] != 'guilt':
                            return f'The {npc_name} refuses to speak with you. Come back when you are sorry for what you have done.'
                        elif npc_name == 'Abyss' and game_progress['feel'] != 'divine terror':
                            return f'You can only communicate with the ABYSS when you are FEELING DIVING TERROR.'
                       
                        # Sanitize user_input if it begins with "talk {npc_name.lower()} "
                        prefix = f"talk {npc_name.lower()} "
                        if user_input.lower().startswith(prefix):
                            user_input = user_input[len(prefix):].strip()

                        if npc_name.lower() == "mermaid" and (night_start >= current_time < morning_start):
                            return "The MERMAID is asleep for the night."
                        elif npc_name.lower() == "astrologer" and (morning_start <= current_time < evening_start):
                            return "The ASTROLOGER is asleep during the day."
                        elif npc_name.lower() == 'deer' and (phase_angle >= 99):
                            return "The DEER spirit ignores you."
                        elif npc_name.lower() == 'stranger':
                            if ((0 < phase_angle < 11) or (20 < phase_angle < 40) or (55 < phase_angle < 65) or (80 < phase_angle <= 100)):
                                return "The STRANGER is asleep."
     
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
    # Get all keys in the session
    keys = session.keys()
    # return(str(keys))
    # Create a list to store all values
    all_values = [session[key] for key in keys]

    # Calculate the total size of all data
    total_size = sum(len(jsonify(session[key]).get_data(as_text=True)) for key in keys)

    game_progress = load_game_progress(session.get('uuid', 'default_uuid'))
    return f"Game progress:\n{game_progress}\n\ntotal_size:\n{total_size}"

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

    # Dictionary of available items in each location
    item_dict = {
        "Summit Observatory": [],
        "Devil's Tail": [],
        "Hallowed Ground": [],
        "Dream Temple": ['pillow'],
        "Hidden Path": [],
        "Hillside Caves": [],
        "Unspoken Hills": [],
        "Western Glassrock Cliffs": [],
        "Sunken Grotto": [],
        "Hermitage": [],
        "Lonesome Path": [],
        "Bath House": ["towel"],
        "Tea Cart": ["tea"],
        "Unspoken Hills": [],
        "Western Glassrock Cliffs": [],
        "Upper Mountain Path": [],
        "Lower Mountain Path": [],
        "Chiron's Cove": [],
        "Mountain Train Station": [],
        "Slime City Train Station": [],
        "Western Shore": [],
        "Library": ["book"],
        "Slime City Uptown": [],
        "Slime City Downtown": [],
        "Slime City Transport Center": [],
        "Slime City Bus Stop": [],
        "Beach Bus Stop": [],
        "Central Shoreline": [],
        "Pier": [],
        "Slime Commons": [],
        "Peace-a-Pizza": ["pizza"],
        "Slime Park": [],
        "Botanical Garden": ["apple"],
        "Odd Beach": [],
        "Your Apartment": ["mirror"],
        "Slime Apartments": [],
        "Confectioner": [],
        "Therapist": [],
        "Eastern Glassrock Cliffs": [],
        "Farm South": [],
        "Town Hall": [],
        "General Store": [], 
        "Casino": [],
        "Club 7 of Clubs": [],
        "Island": []
    }

    # Check if UUID exists in the session, generate one if not
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())
    # Load game_progress from CSV file
    game_progress = load_game_progress(session.get('uuid', 'default_uuid'))

    # Get or initialize the player's inventory from the session
    # 0 = obtainable, 1 = in inventory, 2 = taken out of inventory, 3 = unobtainable
    player_inventory = game_progress.setdefault('inventory', {'apple': 0, 'towel': 0, 'tea': 0, 'mirror': 0, 'book': 0, 'pizza': 0, 'pillow': 0})

    # Load location_dict from CSV file
    location_dict = load_location_from_csv('locations.csv')

    current_location = session.setdefault('location', {'x': 7, 'y': 8})
    current_key = f"{current_location['x']},{current_location['y']}"

    if current_key in location_dict:
        current_place = location_dict[current_key]


    # Check if the user input contains "get"
    if "get" in user_input:
        # Extract the item name after "get"
        item_name = user_input.split("get", 1)[-1].strip().lower()

        # Check if the item name is valid

        if item_name in item_dict[current_place]:
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
                return f"You obtained {item_name.upper()}."
            elif item_status == 1:
                # Item is already in the inventory
                return f"You already have {item_name.upper()} in your inventory."
            elif item_status == 2:
                # Item was given to NPC
                return f"You no longer have {item_name.upper()}."
            else:
                # Item is unobtainable
                return f"{item_name.upper()} is not currently obtainable at {current_place.upper()}."
        elif item_dict[current_place] == '' or item_dict[current_place] == []:
            return "There is nothing for you to GET here."
        else:
            available_items = item_dict[current_place]
            obtainable_items = available_items
            items_to_remove = []

            for item in obtainable_items:
                if player_inventory[item] == 1:
                    items_to_remove.append(item)

            for item in items_to_remove:
                obtainable_items.remove(item)

            if not obtainable_items:
                return f"There is nothing left for you to GET at {current_place.upper()}"
            
            obtainable_items_upper = '\n '.join(available_items).upper()
            return f"You can GET the following at {current_place.upper()}:\n\n{obtainable_items_upper}"
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
    possible_emotions = ['joy', 'guilt', 'divine terror', 'neutral', 'mirth', 'calm', 'petulance', 'wrath', 'sonder', 'jouissance', 'ecstasy', 'vexed']

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
    if not (0 <= x <= 9 and 0 <= y <= 9):
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
    player_inventory = game_progress.setdefault('inventory', {'apple': 0, 'towel': 0, 'tea': 0, 'mirror': 0, 'book': 0, 'pizza': 0, 'pillow': 0})
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

    action_function = action_dict.get(user_input.split()[0], lambda session, user_input: 'ERROR: Command not found. Type \'help\' for a list of commands.')
   
    if (user_input.lower() != 'introspect' and user_input.lower() != 'reset' and user_input.lower() != 'help' and user_input.lower() != 'guide' and user_input.lower() != 'status') and int(game_progress['introspect']) == 0:
        return "Type 'introspect' and press enter to begin your journey."
    else:
        return action_function(session, user_input)

