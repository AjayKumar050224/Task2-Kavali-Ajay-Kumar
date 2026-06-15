// ==========================================================================
// LuxStay Portal Client-Side Application Logic
// ==========================================================================

const API_BASE_URL = ''; // Relative paths since hosted on same origin

// Cache DOM Elements
const roomsContainer = document.getElementById('rooms-container');
const bookingsContainer = document.getElementById('bookings-container');
const roomsCountBadge = document.getElementById('rooms-count');
const bookingsCountBadge = document.getElementById('bookings-count');

const statTotalRooms = document.getElementById('stat-total-rooms');
const statAvailableRooms = document.getElementById('stat-available-rooms');
const statBookedRooms = document.getElementById('stat-booked-rooms');

// Auth Elements
const userPanelName = document.getElementById('user-panel-name');
const btnLogout = document.getElementById('btn-logout');

// Filter Inputs
const filterType = document.getElementById('filter-type');
const filterArea = document.getElementById('filter-area');
const filterMinPrice = document.getElementById('filter-min-price');
const filterMaxPrice = document.getElementById('filter-max-price');
const btnResetFilters = document.getElementById('btn-reset-filters');

// Modal Elements
const bookingModal = document.getElementById('booking-modal');
const btnCloseModal = document.getElementById('btn-close-modal');
const btnCancelBooking = document.getElementById('btn-cancel-booking');
const bookingForm = document.getElementById('booking-form');

const modalRoomId = document.getElementById('modal-room-id');
const modalRoomType = document.getElementById('modal-room-type');
const modalRoomPrice = document.getElementById('modal-room-price');
const formRoomId = document.getElementById('form-room-id');

// Global Date Setups
const checkInInput = document.getElementById('check_in');
const checkOutInput = document.getElementById('check_out');

// Set check-in date minimum to today's date
const today = new Date().toISOString().split('T')[0];
checkInInput.min = today;
checkOutInput.min = today;

// App States
let allRooms = [];
let allBookings = [];

// ==========================================================================
// Initialization & Data Loading
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    checkSession();
    fetchDashboardData();
    setupEventListeners();
});

// Verify the user has an active session; show their name or bounce to login.
async function checkSession() {
    try {
        const response = await fetch('/api/session', { credentials: 'include' });
        const data = await response.json();

        if (!data.authenticated) {
            window.location.href = '/login.html';
            return;
        }

        userPanelName.textContent = data.user.full_name;
    } catch (err) {
        window.location.href = '/login.html';
    }
}

async function fetchDashboardData() {
    try {
        await Promise.all([loadRooms(), loadBookings()]);
        calculateStats();
    } catch (err) {
        showToast('Error loading dashboard data.', 'error');
    }
}

async function loadRooms() {
    roomsContainer.innerHTML = '<div class="loading-spinner">Loading Rooms...</div>';
    
    // Construct Query String for search/filters
    const params = new URLSearchParams();
    if (filterType.value) params.append('type', filterType.value);
    if (filterArea.value) params.append('area', filterArea.value);
    if (filterMinPrice.value) params.append('min_price', filterMinPrice.value);
    if (filterMaxPrice.value) params.append('max_price', filterMaxPrice.value);

    const url = `/rooms?${params.toString()}`;

    try {
        const response = await fetch(url, { credentials: 'include' });
        if (response.status === 401) {
            window.location.href = '/login.html';
            return;
        }
        if (!response.ok) throw new Error('Failed to fetch rooms');
        const rooms = await response.json();
        
        // Dynamically populate the Area dropdown on first load when all rooms are retrieved
        if (filterArea.options.length <= 1 && rooms.length > 0) {
            populateAreaDropdown(rooms);
        }
        
        allRooms = rooms;
        renderRooms(rooms);
    } catch (error) {
        roomsContainer.innerHTML = '<div class="no-data">Failed to load rooms. Please check the backend.</div>';
        throw error;
    }
}

function populateAreaDropdown(rooms) {
    const areas = [...new Set(rooms.map(r => r.area).filter(Boolean))];
    filterArea.innerHTML = '<option value="">All Areas</option>' + 
        areas.map(area => `<option value="${area}">${area}</option>`).join('');
}

async function loadBookings() {
    bookingsContainer.innerHTML = '<div class="loading-spinner">Loading Bookings...</div>';
    try {
        const response = await fetch('/bookings', { credentials: 'include' });
        if (response.status === 401) {
            window.location.href = '/login.html';
            return;
        }
        if (!response.ok) throw new Error('Failed to fetch bookings');
        const bookings = await response.json();
        allBookings = bookings;
        renderBookings(bookings);
    } catch (error) {
        bookingsContainer.innerHTML = '<div class="no-data">Failed to load bookings.</div>';
        throw error;
    }
}

// Calculate Stats dynamically
function calculateStats() {
    // Total rooms stats represents all rooms in rooms.json
    // But since the GET /rooms could be filtered, we do a quick fetch of all rooms if allRooms has filters,
    // or just calculate from the loaded data if we didn't apply any filter.
    // To ensure accuracy, we query the stats based on the general loaded lists
    const total = allRooms.length;
    const available = allRooms.filter(r => r.available).length;
    const booked = allRooms.filter(r => !r.available).length;

    statTotalRooms.textContent = total;
    statAvailableRooms.textContent = available;
    statBookedRooms.textContent = booked;
}

// ==========================================================================
// Rendering Elements
// ==========================================================================

function renderRooms(rooms) {
    roomsCountBadge.textContent = `${rooms.length} ${rooms.length === 1 ? 'Room' : 'Rooms'}`;
    
    if (rooms.length === 0) {
        roomsContainer.innerHTML = '<div class="no-data">No rooms match your filters.</div>';
        return;
    }

    roomsContainer.innerHTML = rooms.map(room => {
        const isAvailable = room.available;
        const statusClass = isAvailable ? 'status-available' : 'status-booked';
        const statusText = isAvailable ? 'Available' : 'Booked';
        
        return `
            <div class="room-card" data-id="${room.room_id}">
                <div class="room-header">
                    <span class="room-title">Room ${room.room_id}</span>
                    <span class="room-type">${room.room_type}</span>
                </div>
                <div class="room-price-tag">
                    <span class="room-price">₹${room.price}</span>
                    <span class="room-unit">/ night</span>
                </div>
                <div class="room-area" style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.75rem; display: flex; align-items: center; gap: 4px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--primary)"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                    <span>${room.area || 'Unknown Location'}</span>
                </div>
                <div class="room-status ${statusClass}">
                    <span class="status-dot"></span>
                    <span>${statusText}</span>
                </div>
                <div class="room-footer">
                    ${isAvailable 
                        ? `<button type="button" class="btn btn-primary btn-book" onclick="openBookingModal(${JSON.stringify(room).replace(/"/g, '&quot;')})">Book Room</button>`
                        : `<button type="button" class="btn btn-secondary" disabled>Unavailable</button>`
                    }
                </div>
            </div>
        `;
    }).join('');
}

function renderBookings(bookings) {
    bookingsCountBadge.textContent = `${bookings.length} ${bookings.length === 1 ? 'Booking' : 'Bookings'}`;

    if (bookings.length === 0) {
        bookingsContainer.innerHTML = '<div class="no-data">No active bookings found.</div>';
        return;
    }

    bookingsContainer.innerHTML = bookings.map(booking => {
        return `
            <div class="booking-card">
                <div class="booking-header">
                    <span class="booking-cust-name">${booking.customer_name}</span>
                    <span class="booking-id-tag">ID: #${booking.booking_id}</span>
                </div>
                <div class="booking-details-grid">
                    <div class="detail-item">
                        <span class="detail-lbl">Room</span>
                        <span class="detail-val">Room ${booking.room_id}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-lbl">Phone</span>
                        <span class="detail-val">${booking.phone}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-lbl">Check In</span>
                        <span class="detail-val">${booking.check_in}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-lbl">Check Out</span>
                        <span class="detail-val">${booking.check_out}</span>
                    </div>
                </div>
                <div class="booking-footer">
                    <span class="booking-time">Booked on: ${booking.timestamp || 'N/A'}</span>
                    <button type="button" class="btn btn-danger btn-sm" onclick="cancelBooking(${booking.booking_id})">
                        Cancel Booking
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// ==========================================================================
// Operations & Actions
// ==========================================================================

// Open Modal
window.openBookingModal = function(room) {
    modalRoomId.textContent = room.room_id;
    modalRoomType.textContent = room.room_type;
    modalRoomPrice.textContent = room.price;
    formRoomId.value = room.room_id;
    
    // Clear previous input fields
    bookingForm.reset();
    
    // Setup date constraints
    checkInInput.value = '';
    checkOutInput.value = '';
    
    bookingModal.classList.add('active');
};

// Close Modal
function closeModal() {
    bookingModal.classList.remove('active');
}

// Create Booking
bookingForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const roomId = parseInt(formRoomId.value);
    const bookingData = {
        room_id: roomId,
        customer_name: document.getElementById('customer_name').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value,
        check_in: checkInInput.value,
        check_out: checkOutInput.value
    };

    try {
        const response = await fetch('/book', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(bookingData)
        });

        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || 'Failed to create booking');
        }

        showToast('Room booked successfully!', 'success');
        closeModal();
        fetchDashboardData();
    } catch (error) {
        showToast(error.message, 'error');
    }
});

// Cancel Booking
window.cancelBooking = async function(bookingId) {
    if (!confirm('Are you sure you want to cancel this booking? This will immediately free up the room.')) {
        return;
    }

    try {
        const response = await fetch(`/booking/${bookingId}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || 'Failed to cancel booking');
        }

        showToast('Booking cancelled successfully.', 'success');
        fetchDashboardData();
    } catch (error) {
        showToast(error.message, 'error');
    }
};

// Setup Listeners
function setupEventListeners() {
    // Live Search filters
    filterType.addEventListener('change', loadRooms);
    filterArea.addEventListener('change', loadRooms);
    filterMinPrice.addEventListener('input', debounce(loadRooms, 300));
    filterMaxPrice.addEventListener('input', debounce(loadRooms, 300));
    
    // Reset filters
    btnResetFilters.addEventListener('click', () => {
        filterType.value = '';
        filterArea.value = '';
        filterMinPrice.value = '';
        filterMaxPrice.value = '';
        loadRooms();
    });

    // Close Modal actions
    btnCloseModal.addEventListener('click', closeModal);
    btnCancelBooking.addEventListener('click', closeModal);

    // Logout
    btnLogout.addEventListener('click', async () => {
        try {
            await fetch('/api/logout', {
                method: 'POST',
                credentials: 'include'
            });
        } catch (err) {
            // Ignore network errors and redirect to login regardless
        }
        window.location.href = '/login.html';
    });
    
    // Close modal when clicking outside card
    bookingModal.addEventListener('click', (e) => {
        if (e.target === bookingModal) closeModal();
    });

    // Set check-out minimum to check-in + 1 day
    checkInInput.addEventListener('change', () => {
        if (checkInInput.value) {
            const nextDay = new Date(checkInInput.value);
            nextDay.setDate(nextDay.getDate() + 1);
            checkOutInput.min = nextDay.toISOString().split('T')[0];
            
            // Adjust check-out value if it's now invalid
            if (checkOutInput.value && checkOutInput.value <= checkInInput.value) {
                checkOutInput.value = checkOutInput.min;
            }
        }
    });
}

// Debounce helper for price filters
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// ==========================================================================
// Custom Notification Toast System
// ==========================================================================

function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Simple icons based on type
    const icon = type === 'success' 
        ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #10b981"><polyline points="20 6 9 17 4 12"></polyline></svg>`
        : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #ef4444"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;

    toast.innerHTML = `
        ${icon}
        <span class="toast-message">${message}</span>
    `;
    
    toastContainer.appendChild(toast);
    
    // Trigger slide in
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Automatically dismiss toast
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
}
