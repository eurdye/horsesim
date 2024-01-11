# DEAD HORSE
A text adventure written in Python using Flask.

DEAD HORSE is a "spiritual" sequel to my 2014 student game *Horse Simulator*. DEAD HORSE is designed to be played in browser and should look fine at resolutions between 720p and 4K. 

### Features
* Exhilarating command line gameplay
* Large game world featuring unique locations
* Real-time time of day and moon phase system
* Smart NPCs based on Eliza chatbot
* Industry-leading text-based horse-themed afterlife simulation software

### Installation Instructions
1. Run `pip install -r requirements.txt` to install the necessary Python modules.
2. Run `source virt/bin/activate` to activate the Python venv. 
3. Run `python server.py` to start the server.
4. Visit 127.0.0.1:5000 in browser to play.

### Todo
* Implement real-time clock
    * ~~Real-time clock~~
    * ~~Moon phases~~
    * Calendar?
    * Tides?
* Add `use` and `give` commands
* Improve dialogue system
    * ~~Implement Eliza chatbot~~
* Add non-chatbot NPCs?
* Add events (observatory new moon, hermitage full moon, grotto low tide, pier high tide)
* Add things to interact with at various locations
    * Make user take the bus or train when going to/from town
    * Add customizable apartment

### Credits
* Eliza chatbot based on [Eliza](https://github.com/wadetb/eliza/tree/master)
