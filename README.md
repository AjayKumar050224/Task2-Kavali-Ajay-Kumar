# Hotel Room Booking Backend API

A production-ready, well-structured Hotel Room Booking Management System Backend API built using Python, Flask, and Flask-CORS. It utilizes a thread-safe JSON-based storage layer to mimic a lightweight database.

---

## Features

1. **Login & Sign Up Portal**: Visitors must sign in (or create an account) before they can access the booking dashboard. Sessions are managed via secure, signed cookies, and passwords are stored as salted hashes (never plaintext).
2. **View Rooms**: Retrieve a list of all hotel rooms.
3. **Search Rooms**:
   - Filter rooms by room type (e.g. `Single`, `Double`, `Suite` - case insensitive).
   - Filter rooms by price range (`min_price` and `max_price`).
4. **Check Room Availability**: Instantly inspect if a room is available (`true` / `false`) by its ID.
5. **Book a Room**: Secure a room with automatic input validation:
   - Validates that the customer name is provided.
   - Validates correct email format (regex check).
   - Validates phone number length and format.
   - Checks room existence and availability (rejects double bookings).
   - Validates date format (`YYYY-MM-DD`), ensuring check-in is today or in the future and check-out is after check-in.
   - Generates a unique booking ID and transaction timestamp.
6. **View Bookings**: Retrieve a complete list of current bookings.
7. **Cancel Booking**: Cancel a booking by ID, which frees up the room and updates its availability back to `true`.

---

## Folder Structure

```text
hotel-booking-api/
│
├── app.py                  # Entry point, configures CORS, error handling, seeds database, auth gating
├── database.py             # Thread-safe read/write actions for JSON storage
├── requirements.txt        # Dependency packages
├── README.md               # API & testing documentation
├── rooms.json              # Persistent rooms data file (temporary database)
├── bookings.json           # Persistent bookings data file (temporary database)
├── users.json              # Persistent user accounts data file (temporary database)
├── routes/
│   ├── __init__.py         # Defines routes as a package
│   ├── auth.py             # Endpoints for registration, login, logout & session check
│   ├── rooms.py            # Endpoints for rooms and availability
│   └── bookings.py         # Endpoints for booking operations and cancellations
└── static/
    ├── login.html           # Login / Sign Up page (shown first to new visitors)
    ├── auth.js              # Client-side logic for login.html
    ├── index.html            # Booking dashboard (requires login)
    ├── script.js             # Client-side logic for index.html
    └── style.css             # Shared styling for both pages
```

---

## Getting Started

### 1. Prerequisites
Ensure you have **Python 3.8+** installed.

### 2. Setup and Install Dependencies
Navigate to the root directory and install dependencies:

```bash
# Optional: Create and activate a virtual environment
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Run the Server
Start the Flask development server:

```bash
python app.py
```
The server will start at **`http://localhost:5000`**.

---

## API Reference & Endpoints

### Authentication

All `/rooms`, `/availability/<id>`, `/book`, `/bookings`, and `/booking/<id>` endpoints require an active login session. The frontend handles this automatically by redirecting unauthenticated visitors to `/login.html`, but when calling the API directly (e.g. with `curl`), you must first log in and reuse the returned session cookie.

#### Register a New Account
* **Endpoint**: `POST /api/register`
* **Content-Type**: `application/json`
* **Request Body**:
  ```json
  {
    "full_name": "Ajay Kumar",
    "email": "ajay@gmail.com",
    "password": "mypassword123"
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "message": "Account created successfully!",
    "user": {
      "user_id": 1,
      "full_name": "Ajay Kumar",
      "email": "ajay@gmail.com"
    }
  }
  ```
* **Validation**: `full_name` is required; `email` must be a valid, unused email address; `password` must be at least 6 characters. A successful registration also logs the user in immediately.

* **Sample Command**:
  ```bash
  curl -X POST -H "Content-Type: application/json" -c cookies.txt \
    -d "{\"full_name\":\"Ajay Kumar\",\"email\":\"ajay@gmail.com\",\"password\":\"mypassword123\"}" \
    http://localhost:5000/api/register
  ```

---

#### Login
* **Endpoint**: `POST /api/login`
* **Content-Type**: `application/json`
* **Request Body**:
  ```json
  {
    "email": "ajay@gmail.com",
    "password": "mypassword123"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "message": "Login successful!",
    "user": {
      "user_id": 1,
      "full_name": "Ajay Kumar",
      "email": "ajay@gmail.com"
    }
  }
  ```
* **Response (401 Unauthorized)** (wrong email or password):
  ```json
  {
    "error": "Unauthorized",
    "message": "Invalid email or password."
  }
  ```

* **Sample Command**:
  ```bash
  curl -X POST -H "Content-Type: application/json" -c cookies.txt \
    -d "{\"email\":\"ajay@gmail.com\",\"password\":\"mypassword123\"}" \
    http://localhost:5000/api/login
  ```

---

#### Check Session Status
* **Endpoint**: `GET /api/session`
* **Response (200 OK, authenticated)**:
  ```json
  {
    "authenticated": true,
    "user": {
      "user_id": 1,
      "full_name": "Ajay Kumar",
      "email": "ajay@gmail.com"
    }
  }
  ```
* **Response (200 OK, not authenticated)**:
  ```json
  { "authenticated": false }
  ```

* **Sample Command**:
  ```bash
  curl -b cookies.txt http://localhost:5000/api/session
  ```

---

#### Logout
* **Endpoint**: `POST /api/logout`
* **Response (200 OK)**:
  ```json
  { "message": "Logged out successfully." }
  ```

* **Sample Command**:
  ```bash
  curl -X POST -b cookies.txt http://localhost:5000/api/logout
  ```

---

### Room & Booking Endpoints

> **Note**: Every endpoint below requires a valid session cookie obtained from `/api/login` or `/api/register` (e.g. add `-b cookies.txt` to each `curl` command below). Requests without a valid session return:
> ```json
> { "error": "Unauthorized", "message": "You must be logged in to perform this action." }
> ```

### 1. View & Search Rooms
* **Endpoint**: `GET /rooms`
* **Query Parameters**:
  - `type` (optional): Filter by room type (`Single`, `Double`, `Suite`). Case-insensitive.
  - `area` (optional): Filter by room area/location (e.g. `Gachibowli`, `Madhapur`). Case-insensitive.
  - `min_price` (optional): Filter rooms with price >= value.
  - `max_price` (optional): Filter rooms with price <= value.
* **Response (200 OK)**:
  ```json
  [
    {
      "room_id": 101,
      "room_type": "Single",
      "price": 1000,
      "available": true,
      "area": "Gachibowli"
    },
    {
      "room_id": 102,
      "room_type": "Double",
      "price": 1800,
      "available": true,
      "area": "Madhapur"
    }
  ]
  ```

* **Sample Command**:
  ```bash
  curl "http://localhost:5000/rooms?type=Single&max_price=1200"
  ```

---

### 2. Check Room Availability
* **Endpoint**: `GET /availability/<room_id>`
* **Response (200 OK)**:
  ```json
  {
    "room_id": 101,
    "room_type": "Single",
    "price": 1000,
    "available": true
  }
  ```
* **Response (404 Not Found)**:
  ```json
  {
    "error": "Not Found",
    "message": "Room with ID 999 not found."
  }
  ```

* **Sample Command**:
  ```bash
  curl http://localhost:5000/availability/101
  ```

---

### 3. Book a Room
* **Endpoint**: `POST /book`
* **Content-Type**: `application/json`
* **Request Body**:
  ```json
  {
    "customer_name": "Ajay",
    "email": "ajay@gmail.com",
    "phone": "9666450275",
    "room_id": 101,
    "check_in": "2026-06-20",
    "check_out": "2026-06-22"
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "message": "Booking successful!",
    "booking": {
      "booking_id": 1,
      "customer_name": "Ajay",
      "email": "ajay@gmail.com",
      "phone": "9666450275",
      "room_id": 101,
      "check_in": "2026-06-20",
      "check_out": "2026-06-22",
      "timestamp": "2026-06-15 13:30:15"
    }
  }
  ```
* **Response (400 Bad Request)** (e.g. invalid date range or room already booked):
  ```json
  {
    "error": "Bad Request",
    "message": "Room with ID 101 is already booked and not available."
  }
  ```

* **Sample Command**:
  ```bash
  curl -X POST -H "Content-Type: application/json" -d "{\"customer_name\":\"Ajay\",\"email\":\"ajay@gmail.com\",\"phone\":\"9666450275\",\"room_id\":101,\"check_in\":\"2026-06-20\",\"check_out\":\"2026-06-22\"}" http://localhost:5000/book
  ```

---

### 4. View All Bookings
* **Endpoint**: `GET /bookings`
* **Response (200 OK)**:
  ```json
  [
    {
      "booking_id": 1,
      "customer_name": "Ajay",
      "email": "ajay@gmail.com",
      "phone": "9666450275",
      "room_id": 101,
      "check_in": "2026-06-20",
      "check_out": "2026-06-22",
      "timestamp": "2026-06-15 13:30:15"
    }
  ]
  ```

* **Sample Command**:
  ```bash
  curl http://localhost:5000/bookings
  ```

---

### 5. Cancel a Booking
* **Endpoint**: `DELETE /booking/<booking_id>`
* **Response (200 OK)**:
  ```json
  {
    "message": "Booking 1 successfully cancelled. Room 101 is now available.",
    "cancelled_booking_id": 1,
    "room_id": 101
  }
  ```
* **Response (404 Not Found)**:
  ```json
  {
    "error": "Not Found",
    "message": "Booking with ID 999 not found."
  }
  ```

* **Sample Command**:
  ```bash
  curl -X DELETE http://localhost:5000/booking/1
  ```

---

## Postman Testing Examples

### Importing as a Collection
You can easily test the API using Postman by creating a new **Collection** called `Hotel Room Booking API` and adding the following requests:

1. **Get All Rooms**:
   - **Method**: `GET`
   - **URL**: `{{base_url}}/rooms`
   - *Test query parameters*: Add key `type` with value `Single` or key `max_price` with value `2000` to test search.

2. **Check Room 101 Availability**:
   - **Method**: `GET`
   - **URL**: `{{base_url}}/availability/101`

3. **Create Booking**:
   - **Method**: `POST`
   - **URL**: `{{base_url}}/book`
   - **Headers**: `Content-Type: application/json`
   - **Body (raw JSON)**:
     ```json
     {
       "customer_name": "Ajay",
       "email": "ajay@gmail.com",
       "phone": "9666450275",
       "room_id": 101,
       "check_in": "2026-06-20",
       "check_out": "2026-06-22"
     }
     ```

4. **Verify Room 101 Availability (Should be False)**:
   - **Method**: `GET`
   - **URL**: `{{base_url}}/availability/101`

5. **Get All Bookings**:
   - **Method**: `GET`
   - **URL**: `{{base_url}}/bookings`

6. **Cancel Booking**:
   - **Method**: `DELETE`
   - **URL**: `{{base_url}}/booking/1`

> **Tip:** You can set a Collection Variable `base_url` to `http://localhost:5000` in Postman so you don't have to type the domain for every request.
