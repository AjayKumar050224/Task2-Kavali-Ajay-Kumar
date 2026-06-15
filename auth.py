import re
from functools import wraps
from datetime import datetime
from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import load_users, save_users

# Define the blueprint for authentication-related routes
auth_bp = Blueprint('auth', __name__)

# Basic email format validation
EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'


def login_required(view_func):
    """
    Decorator to protect API routes.
    Returns 401 Unauthorized JSON if the user does not have an active session.
    """
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({
                "error": "Unauthorized",
                "message": "You must be logged in to perform this action."
            }), 401
        return view_func(*args, **kwargs)
    return wrapped


@auth_bp.route('/api/register', methods=['POST'])
def register():
    """
    Registers a new user account.
    Validates:
    - full_name is required (non-empty)
    - email is required, must be valid format, and must not already be registered
    - password is required and must be at least 6 characters

    Stores the password as a secure hash (never plaintext).
    On success, logs the new user in immediately by creating a session.
    """
    data = request.get_json()
    if not data:
        return jsonify({
            "error": "Bad Request",
            "message": "Request body must be valid JSON."
        }), 400

    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')

    # 1. Validate full name
    if not full_name or not isinstance(full_name, str) or not full_name.strip():
        return jsonify({
            "error": "Bad Request",
            "message": "full_name is required and must be a non-empty string."
        }), 400

    # 2. Validate email format
    if not email or not isinstance(email, str) or not re.match(EMAIL_REGEX, email):
        return jsonify({
            "error": "Bad Request",
            "message": "A valid email address is required."
        }), 400

    # 3. Validate password
    if not password or not isinstance(password, str) or len(password) < 6:
        return jsonify({
            "error": "Bad Request",
            "message": "Password is required and must be at least 6 characters long."
        }), 400

    email_normalized = email.strip().lower()
    users = load_users()

    # 4. Ensure email is not already registered
    if any(u.get('email', '').lower() == email_normalized for u in users):
        return jsonify({
            "error": "Bad Request",
            "message": "An account with this email address already exists."
        }), 400

    # Generate unique user_id (1-based autoincrement integer)
    if users:
        user_id = max(u.get('user_id', 0) for u in users) + 1
    else:
        user_id = 1

    new_user = {
        "user_id": user_id,
        "full_name": full_name.strip(),
        "email": email_normalized,
        "password_hash": generate_password_hash(password),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    users.append(new_user)

    if not save_users(users):
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to save account. Please try again."
        }), 500

    # Automatically log the user in after successful registration
    session['user_id'] = new_user['user_id']
    session['full_name'] = new_user['full_name']
    session['email'] = new_user['email']

    return jsonify({
        "message": "Account created successfully!",
        "user": {
            "user_id": new_user['user_id'],
            "full_name": new_user['full_name'],
            "email": new_user['email']
        }
    }), 201


@auth_bp.route('/api/login', methods=['POST'])
def login():
    """
    Logs a user in using email and password.
    Validates credentials against stored password hash and creates a session.
    """
    data = request.get_json()
    if not data:
        return jsonify({
            "error": "Bad Request",
            "message": "Request body must be valid JSON."
        }), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not isinstance(email, str) or not email.strip():
        return jsonify({
            "error": "Bad Request",
            "message": "Email is required."
        }), 400

    if not password or not isinstance(password, str):
        return jsonify({
            "error": "Bad Request",
            "message": "Password is required."
        }), 400

    email_normalized = email.strip().lower()
    users = load_users()

    user = next((u for u in users if u.get('email', '').lower() == email_normalized), None)

    if not user or not check_password_hash(user.get('password_hash', ''), password):
        return jsonify({
            "error": "Unauthorized",
            "message": "Invalid email or password."
        }), 401

    # Create session
    session['user_id'] = user['user_id']
    session['full_name'] = user['full_name']
    session['email'] = user['email']

    return jsonify({
        "message": "Login successful!",
        "user": {
            "user_id": user['user_id'],
            "full_name": user['full_name'],
            "email": user['email']
        }
    }), 200


@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    """
    Logs the current user out by clearing the session.
    """
    session.clear()
    return jsonify({"message": "Logged out successfully."}), 200


@auth_bp.route('/api/session', methods=['GET'])
def get_session():
    """
    Returns the current authentication status and, if logged in,
    basic details about the logged-in user.
    """
    if session.get('user_id'):
        return jsonify({
            "authenticated": True,
            "user": {
                "user_id": session.get('user_id'),
                "full_name": session.get('full_name'),
                "email": session.get('email')
            }
        }), 200

    return jsonify({"authenticated": False}), 200
