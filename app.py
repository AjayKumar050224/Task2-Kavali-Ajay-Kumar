import os
import json
import logging
import secrets
from flask import Flask, jsonify, session, send_from_directory
from flask_cors import CORS
from database import ROOMS_FILE, BOOKINGS_FILE, USERS_FILE
from routes.rooms import rooms_bp
from routes.bookings import bookings_bp
from routes.auth import auth_bp, login_required

# Set up logging for server side debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_app():
    """
    Application factory pattern.
    Creates and configures the Flask application, registers blueprints, 
    sets up CORS, error handlers, and ensures seed data exists.
    """
    app = Flask(__name__, static_folder='static', static_url_path='')

    # Secret key used to sign session cookies (auth login state).
    # In production, set this via the SECRET_KEY environment variable.
    app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

    # Configure CORS to allow cross-origin requests (essential for frontend integration)
    # supports_credentials is required so session cookies are sent/received correctly.
    CORS(app, supports_credentials=True)

    # Register blueprints for auth, rooms and bookings
    app.register_blueprint(auth_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(bookings_bp)

    # Protect the booking dashboard's data endpoints behind login.
    # (The /api/* auth endpoints themselves remain public.)
    app.view_functions['rooms.get_rooms'] = login_required(app.view_functions['rooms.get_rooms'])
    app.view_functions['rooms.check_availability'] = login_required(app.view_functions['rooms.check_availability'])
    app.view_functions['bookings.book_room'] = login_required(app.view_functions['bookings.book_room'])
    app.view_functions['bookings.get_bookings'] = login_required(app.view_functions['bookings.get_bookings'])
    app.view_functions['bookings.cancel_booking'] = login_required(app.view_functions['bookings.cancel_booking'])

    # Ensure JSON files exist and are initialized properly
    initialize_seed_data()

    # Centralized Error Handlers returning clean JSON responses
    @app.errorhandler(400)
    def bad_request_handler(error):
        logging.warning(f"400 Bad Request: {error}")
        return jsonify({
            "error": "Bad Request",
            "message": getattr(error, 'description', 'The request parameters were invalid or missing.')
        }), 400

    @app.errorhandler(404)
    def not_found_handler(error):
        logging.warning(f"404 Not Found: {error}")
        return jsonify({
            "error": "Not Found",
            "message": getattr(error, 'description', 'The requested resource could not be found.')
        }), 404

    @app.errorhandler(500)
    def internal_server_error_handler(error):
        logging.error(f"500 Internal Server Error: {error}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred on the server. Please try again later."
        }), 500

    @app.route('/', methods=['GET'])
    def home():
        """
        Serves the frontend website.
        If the visitor doesn't have an active session, show the login/sign up
        page first. Logged-in users are served the booking dashboard.
        """
        if not session.get('user_id'):
            return send_from_directory(app.static_folder, 'login.html')
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/login.html', methods=['GET'])
    def login_page():
        """
        Always-accessible route for the login/sign up page.
        If the user is already logged in, send them straight to the dashboard.
        """
        if session.get('user_id'):
            return send_from_directory(app.static_folder, 'index.html')
        return send_from_directory(app.static_folder, 'login.html')

    @app.route('/index.html', methods=['GET'])
    def dashboard_page():
        """
        Always-accessible route for the dashboard page.
        Redirects unauthenticated visitors back to the login page.
        """
        if not session.get('user_id'):
            return send_from_directory(app.static_folder, 'login.html')
        return send_from_directory(app.static_folder, 'index.html')

    return app

def initialize_seed_data():
    """
    Checks if rooms.json, bookings.json, and users.json exist.
    If not, creates them with default initial data.
    """
    default_rooms = [
        {"room_id": 101, "room_type": "Single", "price": 1000, "available": True, "area": "Gachibowli"},
        {"room_id": 102, "room_type": "Double", "price": 1800, "available": True, "area": "Madhapur"},
        {"room_id": 103, "room_type": "Suite", "price": 3500, "available": True, "area": "Banjara Hills"},
        {"room_id": 104, "room_type": "Single", "price": 1100, "available": True, "area": "Gachibowli"},
        {"room_id": 105, "room_type": "Double", "price": 2000, "available": True, "area": "Madhapur"}
    ]

    # Initialize rooms.json if missing or empty
    if not os.path.exists(ROOMS_FILE) or os.path.getsize(ROOMS_FILE) == 0:
        logging.info("Initializing rooms.json with seed data.")
        try:
            with open(ROOMS_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_rooms, f, indent=2)
        except IOError as e:
            logging.error(f"Failed to initialize rooms.json: {e}")

    # Initialize bookings.json if missing or empty
    if not os.path.exists(BOOKINGS_FILE) or os.path.getsize(BOOKINGS_FILE) == 0:
        logging.info("Initializing bookings.json as an empty list.")
        try:
            with open(BOOKINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
        except IOError as e:
            logging.error(f"Failed to initialize bookings.json: {e}")

    # Initialize users.json if missing or empty
    if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) == 0:
        logging.info("Initializing users.json as an empty list.")
        try:
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
        except IOError as e:
            logging.error(f"Failed to initialize users.json: {e}")

app = create_app()

if __name__ == '__main__':
    # Start the Flask development server on port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)
