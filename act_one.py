from flask import Flask, session 

def user_input_parser(user_input):

    # Dictionary to track current location and progress
    locations = session.get('locations', {'beach': True, 'town': False})
    quests = session.get('quests', {'introspect': 0})

    # Introspect
    if user_input == "introspect":
        quests['introspect'] = 1
        session['quests'] = quests
        return("Who are you? A fragile equine body lies heaped beneath you. You do not remember these muscles, this skin. You remember an argument. Fighting. A loss. Feelings, only vague, receding from you even now as your gaze drifts out over the endless sea... You think you should take a LOOK around.")

    # Status and hints
    if user_input == "status":
        return(quests)

    # Returns a description when the player types 'look'
    elif user_input == "look":
        if locations['beach'] == True:
            return('''You are on the Beach. Before you stretches the Endless Ocean\'s purple waves, pounding rhythmically against the shore.
                   Nearby is the PIER, the GROTTO, and the TOWN.''')
        elif locations['town'] == True:
            return('''You are in Slime City center, baby. Hustle, bustle, and some of that old-school funk.
                   Nearby, you see the SHOP, the CASINO, your HOME, the TRAIN, and the BEACH.''')

    # Lists current location
    elif user_input == 'where':
        return(locations)

    # Go to town
    elif user_input == "go town" and locations['town'] is not True:
        locations['town'] = True
        # Set other locations to False
        for key in locations:
            if key != 'town':
               locations[key] = False
        session['locations'] = locations
        return('going to town')
    elif user_input == "go town" and locations['town'] is True:
        return('you are in town alrady')

    # Go to beach
    elif user_input == "go beach" and locations['beach'] is not True:
        locations['beach'] = True
        # Set other locations to False
        for key in locations:
            if key != 'beach':
                locations[key] = False
        session['locations'] = locations
        return('going to the beach')
    elif user_input == "go beach" and locations['beach'] is True:
        return('you are already at the beach')

    # Help text with basic instructions and hints
    elif user_input == "help":
        return("""COMMAND LIST: look, look [object], get [object], go [location/direction], introspect, talk [being]""")
    else:
        return('ERROR: Command not found')
