'''

This code originally from: https://github.com/wadetb/eliza/tree/master

Used under the MIT License below:

MIT License

Copyright (c) 2019 Wade Brainerd

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

'''


import logging
import random
import re
from collections import namedtuple

# Fix Python2/Python3 incompatibility
try: input = raw_input
except NameError: pass

log = logging.getLogger(__name__)


class Key:
    def __init__(self, word, weight, decomps):
        self.word = word
        self.weight = weight
        self.decomps = decomps


class Decomp:
    def __init__(self, parts, save, reasmbs):
        self.parts = parts
        self.save = save
        self.reasmbs = reasmbs
        self.next_reasmb_index = 0


class Eliza:
    def __init__(self):
        self.initials = []
        self.finals = []
        self.quits = []
        self.pres = {}
        self.posts = {}
        self.synons = {}
        self.keys = {}
        self.memory = []

    def load(self, path):
        key = None
        decomp = None
        with open(path) as file:
            for line in file:
                if not line.strip():
                    continue
                tag, content = [part.strip() for part in line.split(':')]
                if tag == 'initial':
                    self.initials.append(content)
                elif tag == 'final':
                    self.finals.append(content)
                elif tag == 'quit':
                    self.quits.append(content)
                elif tag == 'pre':
                    parts = content.split(' ')
                    self.pres[parts[0]] = parts[1:]
                elif tag == 'post':
                    parts = content.split(' ')
                    self.posts[parts[0]] = parts[1:]
                elif tag == 'synon':
                    parts = content.split(' ')
                    self.synons[parts[0]] = parts
                elif tag == 'key':
                    parts = content.split(' ')
                    word = parts[0]
                    weight = int(parts[1]) if len(parts) > 1 else 1
                    key = Key(word, weight, [])
                    self.keys[word] = key
                elif tag == 'decomp':
                    parts = content.split(' ')
                    save = False
                    if parts[0] == '$':
                        save = True
                        parts = parts[1:]
                    decomp = Decomp(parts, save, [])
                    key.decomps.append(decomp)
                elif tag == 'reasmb':
                    parts = content.split(' ')
                    decomp.reasmbs.append(parts)

    def _match_decomp_r(self, parts, words, results):
        if not parts and not words:
            return True
        if not parts or (not words and parts != ['*']):
            return False
        if parts[0] == '*':
            for index in range(len(words), -1, -1):
                results.append(words[:index])
                if self._match_decomp_r(parts[1:], words[index:], results):
                    return True
                results.pop()
            return False
        elif parts[0].startswith('@'):
            root = parts[0][1:]
            if not root in self.synons:
                raise ValueError("Unknown synonym root {}".format(root))
            if not words[0].lower() in self.synons[root]:
                return False
            results.append([words[0]])
            return self._match_decomp_r(parts[1:], words[1:], results)
        elif parts[0].lower() != words[0].lower():
            return False
        else:
            return self._match_decomp_r(parts[1:], words[1:], results)

    def _match_decomp(self, parts, words):
        results = []
        if self._match_decomp_r(parts, words, results):
            return results
        return None

    def _next_reasmb(self, decomp):
        index = decomp.next_reasmb_index
        result = decomp.reasmbs[index % len(decomp.reasmbs)]
        decomp.next_reasmb_index = index + 1
        return result

    def _reassemble(self, reasmb, results):
        output = []
        for reword in reasmb:
            if not reword:
                continue
            if '(' in reword and ')' in reword:
                match = re.search(r'\((\d+)\)', reword)
                if match:
                    index = int(match.group(1))
                    if 1 <= index <= len(results):
                        insert = results[index - 1]
                        for punct in [',', '.', ';']:
                            if punct in insert:
                                insert = insert[:insert.index(punct)]
                        output.extend(insert)
                        continue
            output.append(reword)
        return output

    def _sub(self, words, sub):
        output = []
        for word in words:
            word_lower = word.lower()
            if word_lower in sub:
                output.extend(sub[word_lower])
            else:
                output.append(word)
        return output

    def _match_key(self, words, key):
        for decomp in key.decomps:
            results = self._match_decomp(decomp.parts, words)
            if results is None:
                log.debug('Decomp did not match: %s', decomp.parts)
                continue
            log.debug('Decomp matched: %s', decomp.parts)
            log.debug('Decomp results: %s', results)
            results = [self._sub(words, self.posts) for words in results]
            log.debug('Decomp results after posts: %s', results)
            reasmb = self._next_reasmb(decomp)
            log.debug('Using reassembly: %s', reasmb)
            if reasmb[0] == 'goto':
                goto_key = reasmb[1]
                if not goto_key in self.keys:
                    raise ValueError("Invalid goto key {}".format(goto_key))
                log.debug('Goto key: %s', goto_key)
                return self._match_key(words, self.keys[goto_key])
            output = self._reassemble(reasmb, results)
            if decomp.save:
                self.memory.append(output)
                log.debug('Saved to memory: %s', output)
                continue
            return output
        return None

    def respond(self, text):
        if text.lower() in self.quits:
            return "Goodbye."
        
        # Remove punctuation from the user's input
        text = re.sub(r'[^\w\s]', '', text)

        text = re.sub(r'\s*\.+\s*', ' . ', text)
        text = re.sub(r'\s*,+\s*', ' , ', text)
        text = re.sub(r'\s*;+\s*', ' ; ', text)
        log.debug('After punctuation cleanup: %s', text)

        words = [w for w in text.split(' ') if w]
        log.debug('Input: %s', words)

        words = self._sub(words, self.pres)
        log.debug('After pre-substitution: %s', words)

        keys = [self.keys[w.lower()] for w in words if w.lower() in self.keys]
        keys = sorted(keys, key=lambda k: -k.weight)
        log.debug('Sorted keys: %s', [(k.word, k.weight) for k in keys])

        output = None

        for key in keys:
            output = self._match_key(words, key)
            if output:
                log.debug('Output from key: %s', output)
                break
        if not output:
            if self.memory:
                index = random.randrange(len(self.memory))
                output = self.memory.pop(index)
                log.debug('Output from memory: %s', output)
            else:
                output = self._next_reasmb(self.keys['xnone'].decomps[0])
                log.debug('Output from xnone: %s', output)

        output = " ".join(output)
        output_final = ""
        # Fix spaces before punctuation
        for i in range(len(output)):
            # Check if the current character is a space and the next character is a punctuation mark
            if i < len(output) - 1 and output[i] == ' ' and output[i + 1] in ",.?!":
                # Skip the space
                continue
            
            # Add the current character to the modified string
            output_final += output[i]

        return output_final
    
    def initial(self):
        return random.choice(self.initials)

    def final(self):
        return random.choice(self.finals)

    def run(self):
        print(self.initial())

        while True:
            sent = input('> ')

            output = self.respond(sent)
            if output is None:
                break

            print(output)

        print(self.final())


def main():
    eliza = Eliza()
    eliza.load('doctor.txt')
    eliza.run()

if __name__ == '__main__':
    logging.basicConfig()
    main()
