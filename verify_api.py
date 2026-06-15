import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error

API_URL = "http://127.0.0.1:5000"

def make_request(path, method="GET", data=None):
    """
    Helper function to send HTTP requests to the local Flask server.
    Handles HTTPError exceptions so we can check error response payloads.
    """
    url = f"{API_URL}{path}"
    headers = {"Content-Type": "application/json"}
    
    payload = None
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
        
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.status
            body = response.read().decode("utf-8")
            try:
                return status_code, json.loads(body) if body else {}
            except json.JSONDecodeError:
                return status_code, body
    except urllib.error.HTTPError as e:
        status_code = e.code
        body = e.read().decode("utf-8")
        try:
            return status_code, json.loads(body) if body else {}
        except json.JSONDecodeError:
            return status_code, body
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}")
        return None, None

def run_tests():
    print("=== STARTING HOTEL BOOKING API INTEGRATION TESTS ===\n")
    tests_failed = 0
    tests_passed = 0

    def assert_equals(expected, actual, test_name):
        nonlocal tests_failed, tests_passed
        if expected == actual:
            print(f"[PASS] {test_name}")
            tests_passed += 1
            return True
        else:
            print(f"[FAIL] {test_name}")
            print(f"       Expected: {expected}")
            print(f"       Actual:   {actual}")
            tests_failed += 1
            return False

    # Test 1: Check root website serving
    status, body = make_request("/")
    assert_equals(200, status, "Root endpoint returns 200 OK")
    is_html = "<!DOCTYPE html>" in body if isinstance(body, str) else False
    assert_equals(True, is_html, "Root page serves HTML website")

    # Test 2: View all rooms
    status, body = make_request("/rooms")
    assert_equals(200, status, "GET /rooms returns 200 OK")
    assert_equals(5, len(body) if isinstance(body, list) else 0, "Initial rooms count is 5")

    # Test 3: Search rooms by type (case insensitive)
    status, body = make_request("/rooms?type=single")
    assert_equals(200, status, "GET /rooms?type=single returns 200")
    all_single = all(r.get("room_type") == "Single" for r in body) if isinstance(body, list) else False
    assert_equals(True, all_single, "All returned rooms are of type 'Single'")
    assert_equals(2, len(body) if isinstance(body, list) else 0, "Found 2 Single rooms")

    # Test 4: Search rooms by price range
    status, body = make_request("/rooms?min_price=1500&max_price=2500")
    assert_equals(200, status, "GET /rooms?min_price=1500&max_price=2500 returns 200")
    correct_price = all(1500 <= r.get("price") <= 2500 for r in body) if isinstance(body, list) else False
    assert_equals(True, correct_price, "All returned rooms are in range [1500, 2500]")
    assert_equals(2, len(body) if isinstance(body, list) else 0, "Found 2 rooms in price range [1500, 2500]")

    # Test 4b: Search rooms by area (location)
    status, body = make_request("/rooms?area=gachibowli")
    assert_equals(200, status, "GET /rooms?area=gachibowli returns 200")
    correct_area = all(r.get("area") == "Gachibowli" for r in body) if isinstance(body, list) else False
    assert_equals(True, correct_area, "All returned rooms are in area 'Gachibowli'")
    assert_equals(2, len(body) if isinstance(body, list) else 0, "Found 2 rooms in area 'Gachibowli'")

    # Test 5: Check Room 101 Availability
    status, body = make_request("/availability/101")
    assert_equals(200, status, "GET /availability/101 returns 200")
    assert_equals(True, body.get("available"), "Room 101 is initially available")

    # Test 6: Book Room 101 (Success Case)
    booking_data = {
        "customer_name": "Ajay",
        "email": "ajay@gmail.com",
        "phone": "9666450275",
        "room_id": 101,
        "check_in": "2026-06-20",
        "check_out": "2026-06-22"
    }
    status, body = make_request("/book", method="POST", data=booking_data)
    assert_equals(201, status, "POST /book returns 201 Created for valid data")
    assert_equals("Booking successful!", body.get("message"), "Success message matches")
    booking = body.get("booking", {})
    assert_equals(1, booking.get("booking_id"), "Generated booking ID is 1")
    assert_equals("Ajay", booking.get("customer_name"), "Customer name is Ajay")

    # Test 7: Verify Room 101 Availability is now False
    status, body = make_request("/availability/101")
    assert_equals(200, status, "GET /availability/101 returns 200 after booking")
    assert_equals(False, body.get("available"), "Room 101 availability is now False")

    # Test 8: Attempt Duplicate Booking on Room 101 (Should Fail)
    booking_data_dup = {
        "customer_name": "Vijay",
        "email": "vijay@gmail.com",
        "phone": "9876543210",
        "room_id": 101,
        "check_in": "2026-06-21",
        "check_out": "2026-06-23"
    }
    status, body = make_request("/book", method="POST", data=booking_data_dup)
    assert_equals(400, status, "POST /book returns 400 Bad Request for duplicate booking")
    assert_equals("Room with ID 101 is already booked and not available.", body.get("message"), "Duplicate booking error message matches")

    # Test 9: Book Non-Existent Room (Should Fail)
    booking_data_bad_room = {
        "customer_name": "Vijay",
        "email": "vijay@gmail.com",
        "phone": "9876543210",
        "room_id": 999,
        "check_in": "2026-06-21",
        "check_out": "2026-06-23"
    }
    status, body = make_request("/book", method="POST", data=booking_data_bad_room)
    assert_equals(404, status, "POST /book returns 404 Not Found for non-existent room")
    assert_equals("Room with ID 999 does not exist.", body.get("message"), "Non-existent room error message matches")

    # Test 10: Validation - Invalid Email (Should Fail)
    booking_data_bad_email = {
        "customer_name": "Vijay",
        "email": "bad_email_format",
        "phone": "9876543210",
        "room_id": 102,
        "check_in": "2026-06-21",
        "check_out": "2026-06-23"
    }
    status, body = make_request("/book", method="POST", data=booking_data_bad_email)
    assert_equals(400, status, "POST /book returns 400 Bad Request for invalid email format")
    assert_equals("A valid email address is required.", body.get("message"), "Bad email error message matches")

    # Test 11: Validation - Invalid Phone (Should Fail)
    booking_data_bad_phone = {
        "customer_name": "Vijay",
        "email": "vijay@gmail.com",
        "phone": "abc123456",
        "room_id": 102,
        "check_in": "2026-06-21",
        "check_out": "2026-06-23"
    }
    status, body = make_request("/book", method="POST", data=booking_data_bad_phone)
    assert_equals(400, status, "POST /book returns 400 Bad Request for invalid phone format")
    assert_equals("A valid phone number is required (10-15 digits, optional + prefix).", body.get("message"), "Bad phone error message matches")

    # Test 12: Validation - Check-out date <= Check-in date (Should Fail)
    booking_data_bad_dates = {
        "customer_name": "Vijay",
        "email": "vijay@gmail.com",
        "phone": "9876543210",
        "room_id": 102,
        "check_in": "2026-06-25",
        "check_out": "2026-06-24"
    }
    status, body = make_request("/book", method="POST", data=booking_data_bad_dates)
    assert_equals(400, status, "POST /book returns 400 Bad Request if check-out date is before check-in date")
    assert_equals("check_out date must be after check_in date.", body.get("message"), "Bad date logic error message matches")

    # Test 13: View All Bookings
    status, body = make_request("/bookings")
    assert_equals(200, status, "GET /bookings returns 200 OK")
    assert_equals(1, len(body) if isinstance(body, list) else 0, "Bookings count is 1")

    # Test 14: Cancel Booking
    status, body = make_request("/booking/1", method="DELETE")
    assert_equals(200, status, "DELETE /booking/1 returns 200 OK")
    assert_equals("Booking 1 successfully cancelled. Room 101 is now available.", body.get("message"), "Cancellation message matches")

    # Test 15: Verify Room 101 Availability is True again
    status, body = make_request("/availability/101")
    assert_equals(200, status, "GET /availability/101 returns 200 after cancellation")
    assert_equals(True, body.get("available"), "Room 101 availability is reset to True")

    # Test 16: Cancel non-existent booking (Should Fail)
    status, body = make_request("/booking/999", method="DELETE")
    assert_equals(404, status, "DELETE /booking/999 returns 404 Not Found")
    assert_equals("Booking with ID 999 not found.", body.get("message"), "Non-existent booking cancel error matches")

    print("\n=== INTEGRATION TEST SUMMARY ===")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    return tests_failed == 0

def restore_database_seeds():
    """
    Resets the JSON files to default starting state.
    """
    print("\nRestoring database seeds to default initial state...")
    default_rooms = [
        {"room_id": 101, "room_type": "Single", "price": 1000, "available": True, "area": "Gachibowli"},
        {"room_id": 102, "room_type": "Double", "price": 1800, "available": True, "area": "Madhapur"},
        {"room_id": 103, "room_type": "Suite", "price": 3500, "available": True, "area": "Banjara Hills"},
        {"room_id": 104, "room_type": "Single", "price": 1100, "available": True, "area": "Gachibowli"},
        {"room_id": 105, "room_type": "Double", "price": 2000, "available": True, "area": "Madhapur"}
    ]
    with open(os.path.join(os.path.dirname(__file__), 'rooms.json'), 'w', encoding='utf-8') as f:
        json.dump(default_rooms, f, indent=2)
    with open(os.path.join(os.path.dirname(__file__), 'bookings.json'), 'w', encoding='utf-8') as f:
        json.dump([], f, indent=2)
    print("Database seeds restored successfully.")

if __name__ == "__main__":
    # Start the Flask app as a background subprocess
    print("Starting Flask application subprocess...")
    server_process = subprocess.Popen(
        [sys.executable, "app.py"]
    )
    
    # Wait for the server to bind to port 5000 and initialize
    time.sleep(4.0)
    
    success = False
    try:
        success = run_tests()
    except Exception as e:
        print(f"Test execution encountered an error: {e}")
    finally:
        # Terminate the server subprocess
        print("\nShutting down Flask application subprocess...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Process did not shut down in time, killing it...")
            server_process.kill()
        
        # Restore JSON database seeds to prevent leaving test side-effects
        restore_database_seeds()
        
    sys.exit(0 if success else 1)
