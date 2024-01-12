import eliza

class ElizaBot:
    def __init__(self):
        self.eliza_instance = eliza.Eliza()
        self.eliza_instance.load('eliza.txt')

    def respond(self, user_input):
        return self.eliza_instance.respond(user_input)

class MonkBot:
    def __init__(self):
        self.eliza_instance = eliza.Eliza()
        self.eliza_instance.load('monk.txt')

    def respond(self, user_input):
        return self.eliza_instance.respond(user_input)

class AstrologerBot:
    def __init__(self):
        self.eliza_instance = eliza.Eliza()
        self.eliza_instance.load('astrologer.txt')

    def respond(self, user_input):
        return self.eliza_instance.respond(user_input)


