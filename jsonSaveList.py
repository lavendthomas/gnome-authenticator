import json
import os

def save(data, file='messages.json'):
    """data shoud be a dict
    """
    with open(file, 'w') as line:
        json.dump(data, line)

def load(file='messages.json'):
    """Returns a list
    """
    # Creates the save file if it does not exists
    if not os.path.exists(file):
        open(file, 'w').close()

    with open(file, 'r') as line:
        content = line.readline()
        if content == '' :
            return list()
        else :
            return json.loads(content)
