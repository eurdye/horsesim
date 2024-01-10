import eliza

class ElizaBot:
    def __init__(self):
        self.eliza_instance = eliza.Eliza()
        self.eliza_instance.load('doctor.txt')

    def respond(self, user_input):
        return self.eliza_instance.respond(user_input)
