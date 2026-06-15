import os
import json
import threading

# Define paths to JSON files relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOMS_FILE = os.path.join(BASE_DIR, 'rooms.json')
BOOKINGS_FILE = os.path.join(BASE_DIR, 'bookings.json')
USERS_FILE = os.path.join(BASE_DIR, 'users.json')

# Create a global thread lock to prevent concurrent write race conditions and corruption
db_lock = threading.Lock()

def load_rooms():
    """
    Thread-safely loads room data from rooms.json.
    If the file doesn't exist, returns an empty list.
    """
    with db_lock:
        if not os.path.exists(ROOMS_FILE):
            return []
        try:
            with open(ROOMS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

def save_rooms(rooms):
    """
    Thread-safely saves room data to rooms.json.
    """
    with db_lock:
        try:
            with open(ROOMS_FILE, 'w', encoding='utf-8') as f:
                json.dump(rooms, f, indent=2)
            return True
        except IOError:
            return False

def load_bookings():
    """
    Thread-safely loads booking data from bookings.json.
    If the file doesn't exist, returns an empty list.
    """
    with db_lock:
        if not os.path.exists(BOOKINGS_FILE):
            return []
        try:
            with open(BOOKINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

def save_bookings(bookings):
    """
    Thread-safely saves booking data to bookings.json.
    """
    with db_lock:
        try:
            with open(BOOKINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(bookings, f, indent=2)
            return True
        except IOError:
            return False

def load_users():
    """
    Thread-safely loads user account data from users.json.
    If the file doesn't exist, returns an empty list.
    """
    with db_lock:
        if not os.path.exists(USERS_FILE):
            return []
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

def save_users(users):
    """
    Thread-safely saves user account data to users.json.
    """
    with db_lock:
        try:
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2)
            return True
        except IOError:
            return False
