const API_BASE_URL = "";

async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem("access_token");

    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {})
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(
        `${API_BASE_URL}${endpoint}`,
        {
            ...options,
            headers
        }
    );

    let data = null;

    try {
        data = await response.json();
    } catch (error) {
        data = null;
    }

    if (!response.ok) {
        const message =
            data?.detail ||
            "Something went wrong. Please try again.";

        throw new Error(message);
    }

    return data;
}


/* ============================================================
   AUTHENTICATION
   ============================================================ */

async function loginUser(email, password) {
    return apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify({
            email,
            password
        })
    });
}


async function registerUser(
    email,
    password,
    confirmPassword
) {
    return apiRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify({
            email,
            password,
            confirm_password: confirmPassword
        })
    });
}


async function getCurrentUser() {
    return apiRequest(
        "/auth/me",
        {
            method: "GET"
        }
    );
}


/* ============================================================
   PRODUCTS
   ============================================================ */

async function getProducts(
    skip = 0,
    limit = 100
) {
    return apiRequest(
        `/products/?skip=${skip}&limit=${limit}`,
        {
            method: "GET"
        }
    );
}


async function getProduct(productId) {
    return apiRequest(
        `/products/${productId}`,
        {
            method: "GET"
        }
    );
}


async function createProduct(
    name,
    price,
    stockQuantity
) {
    return apiRequest(
        "/products/",
        {
            method: "POST",
            body: JSON.stringify({
                name,
                price,
                stock_quantity: stockQuantity
            })
        }
    );
}


async function updateProduct(
    productId,
    name,
    price,
    stockQuantity
) {
    return apiRequest(
        `/products/${productId}`,
        {
            method: "PATCH",
            body: JSON.stringify({
                name,
                price,
                stock_quantity: stockQuantity
            })
        }
    );
}


async function deleteProduct(
    productId
) {
    return apiRequest(
        `/products/${productId}`,
        {
            method: "DELETE"
        }
    );
}


/* ============================================================
   ORDERS
   ============================================================ */

async function getOrders() {
    return apiRequest(
        "/orders/",
        {
            method: "GET"
        }
    );
}


async function getOrder(orderId) {
    return apiRequest(
        `/orders/${orderId}`,
        {
            method: "GET"
        }
    );
}

/* USERS */

async function getUsers() {
    return apiRequest(
        "/users/",
        {
            method: "GET"
        }
    );
}


async function getUser(userId) {
    return apiRequest(
        `/users/${userId}`,
        {
            method: "GET"
        }
    );
}

/* EVENTS */

async function getEvents() {
    return apiRequest(
        "/events/",
        {
            method: "GET"
        }
    );
}

async function getEvent(eventId) {
    return apiRequest(
        `/events/${eventId}`,
        {
            method: "GET"
        }
    );
}

/* NOTIFICATIONS */

async function getNotifications() {
    return apiRequest(
        "/notifications/",
        {
            method: "GET"
        }
    );
}

async function getNotification(notificationId) {
    return apiRequest(
        `/notifications/${notificationId}`,
        {
            method: "GET"
        }
    );
}

async function markNotificationAsRead(notificationId) {
    return apiRequest(
        `/notifications/${notificationId}/read`,
        {
            method: "PATCH"
        }
    );
}

async function markAllNotificationsAsRead() {
    return apiRequest(
        "/notifications/read-all",
        {
            method: "PATCH"
        }
    );
}