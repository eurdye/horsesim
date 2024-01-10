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
    if current_location['x'] == 0 and current_location['y'] == 0:
        return "You reach the peak of the MOUNTAIN. At the summit lies the OBSERVATORY. To your SOUTH is the MOUNTAIN PATH back down."
    elif current_location['x'] == 0 and current_location['y'] == 1:
        return "You are on the MOUNTAIN PATH. To your NORTH lies the SUMMIT OBSERVATORY. To the EAST is the TEMPLE OF FIRE."
    elif current_location['x'] == 0 and current_location['y'] == 2:
        return "You are at X=0, Y=2."
    elif current_location['x'] == 0 and current_location['y'] == 3:
        return "You are at X=0, Y=3."
    elif current_location['x'] == 0 and current_location['y'] == 4:
        return "You are at X=0, Y=4."
    elif current_location['x'] == 0 and current_location['y'] == 5:
        return "You are at X=0, Y=5."
    elif current_location['x'] == 0 and current_location['y'] == 6:
        return "You are at X=0, Y=6."
    elif current_location['x'] == 0 and current_location['y'] == 7:
        return "You are at X=0, Y=7."
    elif current_location['x'] == 0 and current_location['y'] == 8:
        return "You are at X=0, Y=8."
    elif current_location['x'] == 1 and current_location['y'] == 0:
        return "You are at X=0, Y=0."
    elif current_location['x'] == 1 and current_location['y'] == 1:
        return "You are at the TEMPLE OF FIRE. To your WEST lies the MOUNTAIN PATH to the SUMMIT OBSERVATORY. To your EAST lies the MOUNTAIN PATH to the HERMITAGE. To your SOUTH lies the MONASTERY."
    elif current_location['x'] == 1 and current_location['y'] == 2:
        return "You are at the MONASTERY. To your NORTH lies the TEMPLE OF FIRE. To your SOUTH lies the TEA CART."
    elif current_location['x'] == 1 and current_location['y'] == 3:
        return "You are at the TEA CART. To your NORTH lies the MONASTERY. To your EAST lies the BATH HOUSE."
    elif current_location['x'] == 1 and current_location['y'] == 4:
        return "You are at X=0, Y=4."
    elif current_location['x'] == 1 and current_location['y'] == 5:
        return "You are at X=0, Y=5."
    elif current_location['x'] == 1 and current_location['y'] == 6:
        return "You are at X=0, Y=6."
    elif current_location['x'] == 1 and current_location['y'] == 7:
        return "You are on the WESTERN GLASSROCK CLIFFS. To your SOUTH lies the MYSTERIOUS GROTTO. To the EAST lies more WESTERN GLASSROCK CLIFFS."
    elif current_location['x'] == 1 and current_location['y'] == 8:
        return "You are at the MYSTERIOUS GROTTO in the WESTERN BEACH. To the EAST lies the IMPENETRABLE OCEAN. To your NORTH are the WESTERN GLASSROCK CLIFFS."
    elif current_location['x'] == 2 and current_location['y'] == 0:
        return "You are at the MOUNTAINTOP HERMITAGE. To your SOUTH lies the MOUNTAIN PATH."
    elif current_location['x'] == 2 and current_location['y'] == 1:
        return "You are on the MOUNTAIN PATH. To your NORTH lies the HERMITAGE. To your WEST lies the TEMPLE OF FIRE."
    elif current_location['x'] == 2 and current_location['y'] == 2:
        return "You are at X=0, Y=2."
    elif current_location['x'] == 2 and current_location['y'] == 3:
        return "You are at the BATH HOUSE. To your WEST lies the TEA CART. To your EAST lies the MOUNTAIN PATH."
    elif current_location['x'] == 2 and current_location['y'] == 4:
        return "You are at X=0, Y=4."
    elif current_location['x'] == 2 and current_location['y'] == 5:
        return "You are at X=0, Y=5."
    elif current_location['x'] == 2 and current_location['y'] == 6:
        return "You are at X=0, Y=6."
    elif current_location['x'] == 2 and current_location['y'] == 7:
        return "You are on the WESTERN GLASSROCK CLIFFS. To your WEST lies more GLASSROCK CLIFFS. To your EAST lies the BEACH."
    elif current_location['x'] == 2 and current_location['y'] == 8:
        return "You are at X=0, Y=8."
    elif current_location['x'] == 3 and current_location['y'] == 0:
        return "You are at X=0, Y=0."
    elif current_location['x'] == 3 and current_location['y'] == 1:
        return "You are at X=0, Y=1."
    elif current_location['x'] == 3 and current_location['y'] == 2:
        return "You are at X=0, Y=2."
    elif current_location['x'] == 3 and current_location['y'] == 3:
        return "You are on the MOUNTAIN PATH. To the WEST lies the BATH HOUSE. To the EAST is the TRAIN STATION."
    elif current_location['x'] == 3 and current_location['y'] == 4:
        return "You are at X=0, Y=4."
    elif current_location['x'] == 3 and current_location['y'] == 5:
        return "You are at X=0, Y=5."
    elif current_location['x'] == 3 and current_location['y'] == 6:
        return "You are at X=0, Y=6."
    elif current_location['x'] == 3 and current_location['y'] == 7:
        return "You are on the WESTERN BEACH. To the WEST lies the GLASSROCK CLIFFS. To the EAST lies more BEACH."
    elif current_location['x'] == 3 and current_location['y'] == 8:
        return "You are at X=0, Y=8."
    elif current_location['x'] == 4 and current_location['y'] == 0:
        return "You are at X=0, Y=0."
    elif current_location['x'] == 4 and current_location['y'] == 1:
        return "You are at X=0, Y=1."
    elif current_location['x'] == 4 and current_location['y'] == 2:
        return "You are at X=0, Y=2."
    elif current_location['x'] == 4 and current_location['y'] == 3:
        return "You are at the TRAIN STATION. Here you can RIDE TRAIN WEST to get to the MOUNTAIN PATH, or RIDE TRAIN EAST to go to SLIME CITY, or RIDE TRAIN SOUTH to visit the FARM."
    elif current_location['x'] == 4 and current_location['y'] == 4:
        return "You are on the FARM. To your NORTH lies the TRAIN STATION. To the SOUTH is more FARM land. To your EAST is SLIME CITY."
    elif current_location['x'] == 4 and current_location['y'] == 5:
        return "You are on the FARM. To your NORTH is more FARM land. To your EAST is the BOTANICAL GARDEN."
    elif current_location['x'] == 4 and current_location['y'] == 6:
        return "You are at X=0, Y=6."
    elif current_location['x'] == 4 and current_location['y'] == 7:
        return "You are on the BEACH. To your WEST and EAST stretch more BEACH."
    elif current_location['x'] == 4 and current_location['y'] == 8:
        return "You are at X=0, Y=8."
    elif current_location['x'] == 5 and current_location['y'] == 0:
        return "You are at X=0, Y=0."
    elif current_location['x'] == 5 and current_location['y'] == 1:
        return "You are at X=0, Y=1."
    elif current_location['x'] == 5 and current_location['y'] == 2:
        return "You are at the COMMONS. To the EAST lies your APARTMENT. To the SOUTH is SLIME CITY."
    elif current_location['x'] == 5 and current_location['y'] == 3:
        return "You are in SLIME CITY. To your NORTH is the COMMONS. To the WEST is the TRAIN STATION. To the SOUTH and EAST is more SLIME CITY."
    elif current_location['x'] == 5 and current_location['y'] == 4:
        return "You are in SLIME CITY. To your NORTH and EAST is more SLIME CITY. To the WEST is the FARM. To the SOUTH is the BOTANICAL GARDEN."
    elif current_location['x'] == 5 and current_location['y'] == 5:
        return "You are at the BOTANICAL GARDEN. To the NORTH is SLIME CITY. To the WEST is the FARM. To the SOUTH is the BUS STATION to the BEACH. To the EAST is more BOTANICAL GARDEN."
    elif current_location['x'] == 5 and current_location['y'] == 6:
        return "You are at the BUS STATION. You can RIDE BUS to go the BEACH, or go NORTH to visit the BOTANICAL GARDEN."
    elif current_location['x'] == 5 and current_location['y'] == 7:
        return '''You are on the BEACH. You see more BEACH stretching to the EAST and WEST. To your NORTH is the BUS STATION. To the SOUTH is the PIER.'''
    elif current_location['x'] == 5 and current_location['y'] == 8:
        return "You are at the PIER. To your NORTH lies the BEACH."
    elif current_location['x'] == 6 and current_location['y'] == 0:
        return "You are at X=0, Y=0."
    elif current_location['x'] == 6 and current_location['y'] == 1:
        return "You are at X=0, Y=1."
    elif current_location['x'] == 6 and current_location['y'] == 2:
        return "You are at your APARTMENT in NORTHERN SLIME CITY. To the WEST lies the COMMONS. To the EAST lies the TOWN HALL. To the SOUTH is SLIME CITY."
    elif current_location['x'] == 6 and current_location['y'] == 3:
        return "You are in SLIME CITY. To the NORTH is your APARTMENT. To the WEST and SOUTH is more SLIME CITY. To the EAST is the STORE."
    elif current_location['x'] == 6 and current_location['y'] == 4:
        return "You are in SLIME CITY. To the NORTH and WEST is more SLIME CITY. To the SOUTH is the BOTANICAL GARDEN. To the EAST is the CASINO."
    elif current_location['x'] == 6 and current_location['y'] == 5:
        return "You are in the BOTANICAL GARDEN. To the NORTH is SLIME CITY. To the WEST is more BOTANICAL GARDEN. To the EAST is the CLUB."
    elif current_location['x'] == 6 and current_location['y'] == 6:
        # return '''You are in Slime City center, baby. Hustle, bustle, and some of that old-school funk. Nearby, you see the SHOP, the CASINO, your HOME, the TRAIN, and the BEACH.'''
        return "Inaccessible."
    elif current_location['x'] == 6 and current_location['y'] == 7:
        return '''You are on the BEACH. Before you stretches the Endless Ocean\'s purple waves, pounding rhythmically against the shore. You see more BEACH to the WEST. To the EAST are the impenetrable GLASSROCK CLIFFS.'''
    elif current_location['x'] == 6 and current_location['y'] == 8:
        return "You are at X=0, Y=8."
    elif current_location['x'] == 7 and current_location['y'] == 0:
        return "You are at X=0, Y=0."
    elif current_location['x'] == 7 and current_location['y'] == 1:
        return "You are at X=0, Y=1."
    elif current_location['x'] == 7 and current_location['y'] == 2:
        return "You are at the TOWN HALL. To the WEST is your APARTMENT. To the SOUTH is the STORE."
    elif current_location['x'] == 7 and current_location['y'] == 3:
        return "You are at the STORE. To the NORTH is the TOWN HALL. To the WEST is SLIME CITY. To the SOUTH is the CASINO."
    elif current_location['x'] == 7 and current_location['y'] == 4:
        return "You are at the CASINO. To the NORTH is the STORE. To the WEST is SLIME CITY. To the SOUTH is the CLUB."
    elif current_location['x'] == 7 and current_location['y'] == 5:
        return "You are at the CLUB. To the NORTH is the CASINO. To the WEST is the BOTANICAL GARDEN."
    elif current_location['x'] == 7 and current_location['y'] == 6:
        return "You are at X=0, Y=6."
    elif current_location['x'] == 7 and current_location['y'] == 7:
        return "You are at the EASTERN GLASSROCK CLIFFS. To the WEST is the BEACH. You think you see an ISLAND to the SOUTHEAST, but you're not sure how to get there."
    elif current_location['x'] == 7 and current_location['y'] == 8:
        return "You are at X=0, Y=8."
    elif current_location['x'] == 8 and current_location['y'] == 0:
        return "You are at X=0, Y=0."
    elif current_location['x'] == 8 and current_location['y'] == 1:
        return "You are at X=0, Y=1."
    elif current_location['x'] == 8 and current_location['y'] == 2:
        return "You are at X=0, Y=2."
    elif current_location['x'] == 8 and current_location['y'] == 3:
        return "You are at X=0, Y=3."
    elif current_location['x'] == 8 and current_location['y'] == 4:
        return "You are at X=0, Y=4."
    elif current_location['x'] == 8 and current_location['y'] == 5:
        return "You are at X=0, Y=5."
    elif current_location['x'] == 8 and current_location['y'] == 6:
        return "You are at X=0, Y=6."
    elif current_location['x'] == 8 and current_location['y'] == 7:
        return "You are at X=0, Y=7."
    elif current_location['x'] == 8 and current_location['y'] == 8:
        return "You are at X=0, Y=8."
    else:
        return "You are in an unknown location."

# Show user's x, y coords when they type 'where'
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
        return "Where? Use \'go [north/south/east/west]\' to move in the specified direction."

    # Check if the new location is within valid bounds (0 to 9)
    if not (0 <= current_location['x'] <= 8 and 0 <= current_location['y'] <= 8):
        # If not within bounds, revert the move and return an error message
        session['location'] = prev_location
        return f"You can\'t go {direction.upper()} from here."

    # Check if the new location is in the list of invalid coordinates
    invalid_coordinates = [(0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8), (1, 0), (1, 4), (1, 5), (1, 6), (2, 2), (2, 4), (2, 5), (2, 6), (2, 8), (3, 0), (3, 1), (3, 2), (3, 4), (3, 5), (3, 6), (3, 8), (4, 0), (4, 1), (4, 2), (4, 6), (4, 8), (5, 0), (5, 1), (6, 0), (6, 1), (6, 6), (6, 8), (7, 0), (7, 1), (7, 6), (7, 8), (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7)]  # Add your list of invalid (x, y) coordinates here
    if (current_location['x'], current_location['y']) in invalid_coordinates:
        # If in the list, revert the move and return an error message
        session['location'] = prev_location
        return f"You can\'t go {direction.upper()} from here."

    session['location'] = current_location
    if prev_location != current_location:
        return f'You head {direction.upper()}.\n\n' + look_action(session, user_input)
    else:
        return f'Already at {direction.upper()}.'

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

