import re
from datetime import datetime, date
from flask import Blueprint, jsonify, request
from database import load_rooms, save_rooms, load_bookings, save_bookings

# Define the blueprint for booking-related routes
bookings_bp = Blueprint('bookings', __name__)

# Regular expressions for validation
EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'
# Validates standard 10-digit mobile number, or international format with leading + and 10-15 digits
PHONE_REGEX = r'^\+?\d{10,15}$'

def validate_date(date_str):
    """
    Helper to validate date format (YYYY-MM-DD) and return datetime.date object.
    Returns None if validation fails.
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

@bookings_bp.route('/book', methods=['POST'])
def book_room():
    """
    Books a hotel room.
    Validates:
    - Customer name is required (non-empty)
    - Valid email format
    - Valid phone number (10 to 15 digits, optional leading +)
    - Check-in and Check-out dates are valid, check-in is today or in the future, check-out is after check-in
    - Room must exist
    - Room must be available (available = True)
    
    Generates a unique booking ID and a booking timestamp.
    Sets the room's availability to False.
    """
    data = request.get_json()
    if not data:
        return jsonify({
            "error": "Bad Request",
            "message": "Request body must be valid JSON."
        }), 400

    # Extract fields
    customer_name = data.get('customer_name')
    email = data.get('email')
    phone = data.get('phone')
    room_id = data.get('room_id')
    check_in_str = data.get('check_in')
    check_out_str = data.get('check_out')

    # 1. Validate customer name
    if not customer_name or not isinstance(customer_name, str) or not customer_name.strip():
        return jsonify({
            "error": "Bad Request",
            "message": "customer_name is required and must be a non-empty string."
        }), 400

    # 2. Validate email format
    if not email or not isinstance(email, str) or not re.match(EMAIL_REGEX, email):
        return jsonify({
            "error": "Bad Request",
            "message": "A valid email address is required."
        }), 400

    # 3. Validate phone number format
    if not phone or not isinstance(phone, str) or not re.match(PHONE_REGEX, phone):
        return jsonify({
            "error": "Bad Request",
            "message": "A valid phone number is required (10-15 digits, optional + prefix)."
        }), 400

    # 4. Validate room_id presence and type
    if room_id is None:
        return jsonify({
            "error": "Bad Request",
            "message": "room_id is required."
        }), 400
    try:
        room_id = int(room_id)
    except (ValueError, TypeError):
        return jsonify({
            "error": "Bad Request",
            "message": "room_id must be a valid integer."
        }), 400

    # 5. Validate dates
    if not check_in_str or not check_out_str:
        return jsonify({
            "error": "Bad Request",
            "message": "Both check_in and check_out dates are required."
        }), 400

    check_in_date = validate_date(check_in_str)
    check_out_date = validate_date(check_out_str)

    if not check_in_date:
        return jsonify({
            "error": "Bad Request",
            "message": "check_in date must be in YYYY-MM-DD format."
        }), 400

    if not check_out_date:
        return jsonify({
            "error": "Bad Request",
            "message": "check_out date must be in YYYY-MM-DD format."
        }), 400

    # Date business logic validations
    today = date.today()
    if check_in_date < today:
        return jsonify({
            "error": "Bad Request",
            "message": "check_in date cannot be in the past."
        }), 400

    if check_out_date <= check_in_date:
        return jsonify({
            "error": "Bad Request",
            "message": "check_out date must be after check_in date."
        }), 400

    # Load rooms and bookings
    rooms = load_rooms()
    bookings = load_bookings()

    # Find the requested room
    room = next((r for r in rooms if r.get('room_id') == room_id), None)
    
    # 6. Validate Room Exists
    if not room:
        return jsonify({
            "error": "Not Found",
            "message": f"Room with ID {room_id} does not exist."
        }), 404

    # 7. Validate Room Availability
    if not room.get('available', False):
        return jsonify({
            "error": "Bad Request",
            "message": f"Room with ID {room_id} is already booked and not available."
        }), 400

    # Generate unique booking_id (1-based autoincrement integer)
    if bookings:
        booking_id = max(b.get('booking_id', 0) for b in bookings) + 1
    else:
        booking_id = 1

    # Get current timestamp
    booking_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create new booking
    new_booking = {
        "booking_id": booking_id,
        "customer_name": customer_name.strip(),
        "email": email.strip(),
        "phone": phone.strip(),
        "room_id": room_id,
        "check_in": check_in_str,
        "check_out": check_out_str,
        "timestamp": booking_timestamp
    }

    # Add booking and set room availability to False
    bookings.append(new_booking)
    room['available'] = False

    # Save data back to files
    if not save_rooms(rooms) or not save_bookings(bookings):
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to save data. Please try again."
        }), 500

    return jsonify({
        "message": "Booking successful!",
        "booking": new_booking
    }), 201


@bookings_bp.route('/bookings', methods=['GET'])
def get_bookings():
    """
    Retrieves all hotel room bookings.
    """
    bookings = load_bookings()
    return jsonify(bookings), 200


@bookings_bp.route('/booking/<int:booking_id>', methods=['DELETE'])
def cancel_booking(booking_id):
    """
    Cancels an existing booking.
    Re-enables room availability for the associated room_id.
    """
    bookings = load_bookings()
    
    # Find the booking by booking_id
    booking_idx = next((i for i, b in enumerate(bookings) if b.get('booking_id') == booking_id), -1)
    
    if booking_idx == -1:
        return jsonify({
            "error": "Not Found",
            "message": f"Booking with ID {booking_id} not found."
        }), 404

    booking = bookings[booking_idx]
    room_id = booking.get('room_id')

    # Remove the booking
    bookings.pop(booking_idx)

    # Load rooms and mark the room as available again
    rooms = load_rooms()
    room = next((r for r in rooms if r.get('room_id') == room_id), None)
    if room:
        room['available'] = True

    # Save both updates
    if not save_rooms(rooms) or not save_bookings(bookings):
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to update cancellation data."
        }), 500

    return jsonify({
        "message": f"Booking {booking_id} successfully cancelled. Room {room_id} is now available.",
        "cancelled_booking_id": booking_id,
        "room_id": room_id
    }), 200
