import json

def check_login(username, password):
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
        return username in users and users[username] == password
    except:
        return False
