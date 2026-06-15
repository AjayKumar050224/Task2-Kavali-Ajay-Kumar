from flask import Blueprint, jsonify, request
from database import load_rooms

# Define the blueprint for room-related routes
rooms_bp = Blueprint('rooms', __name__)

@rooms_bp.route('/rooms', methods=['GET'])
def get_rooms():
    """
    Retrieves a list of all hotel rooms.
    Supports optional query parameters for filtering:
    - type: search by room type (case-insensitive, e.g., 'Single', 'double')
    - min_price: filter rooms with price greater than or equal to min_price
    - max_price: filter rooms with price less than or equal to max_price
    """
    rooms = load_rooms()
    
    # Extract query parameters
    room_type = request.args.get('type')
    min_price_str = request.args.get('min_price')
    max_price_str = request.args.get('max_price')
    area = request.args.get('area')
    
    filtered_rooms = rooms

    # Filter by room type if specified
    if room_type:
        filtered_rooms = [
            r for r in filtered_rooms 
            if r.get('room_type', '').lower() == room_type.lower()
        ]

    # Filter by area if specified
    if area:
        filtered_rooms = [
            r for r in filtered_rooms 
            if r.get('area', '').lower() == area.lower()
        ]

    # Filter by minimum price if specified
    if min_price_str is not None:
        try:
            min_price = float(min_price_str)
            filtered_rooms = [
                r for r in filtered_rooms 
                if r.get('price', 0) >= min_price
            ]
        except ValueError:
            return jsonify({
                "error": "Bad Request",
                "message": "min_price must be a valid number."
            }), 400

    # Filter by maximum price if specified
    if max_price_str is not None:
        try:
            max_price = float(max_price_str)
            filtered_rooms = [
                r for r in filtered_rooms 
                if r.get('price', 0) <= max_price
            ]
        except ValueError:
            return jsonify({
                "error": "Bad Request",
                "message": "max_price must be a valid number."
            }), 400

    return jsonify(filtered_rooms), 200


@rooms_bp.route('/availability/<int:room_id>', methods=['GET'])
def check_availability(room_id):
    """
    Checks if a room is available for booking.
    Returns 200 OK with availability status, or 404 Not Found if the room doesn't exist.
    """
    rooms = load_rooms()
    
    # Find the room by room_id
    room = next((r for r in rooms if r.get('room_id') == room_id), None)
    
    if not room:
        return jsonify({
            "error": "Not Found",
            "message": f"Room with ID {room_id} not found."
        }), 404

    return jsonify({
        "room_id": room['room_id'],
        "room_type": room.get('room_type'),
        "price": room.get('price'),
        "available": room.get('available', False)
    }), 200
