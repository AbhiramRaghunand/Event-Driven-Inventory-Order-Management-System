/**
 * Save authentication information.
 */
function saveAuth(token, user = null) {

    localStorage.setItem(
        "access_token",
        token
    );

    if (user) {

        localStorage.setItem(
            "current_user",
            JSON.stringify(user)
        );
    }
}


/**
 * Get authentication token.
 */
function getToken() {

    return localStorage.getItem(
        "access_token"
    );
}


/**
 * Get stored user information.
 */
function getStoredUser() {

    const user =
        localStorage.getItem(
            "current_user"
        );

    if (!user) {
        return null;
    }

    try {

        return JSON.parse(user);

    } catch (error) {

        return null;
    }
}


/**
 * Check whether the user has an authentication token.
 */
function isLoggedIn() {

    return Boolean(
        localStorage.getItem(
            "access_token"
        )
    );
}


/**
 * Remove authentication information.
 */
function logout() {

    localStorage.removeItem(
        "access_token"
    );

    localStorage.removeItem(
        "current_user"
    );

    window.location.href =
        "/frontend/pages/login/login.html";
}


/**
 * Require authentication for a page.
 *
 * We will use this on protected pages such as
 * Dashboard, Products, Orders, etc.
 */
function requireAuth() {

    if (!isLoggedIn()) {

        window.location.href =
            "/frontend/pages/login/login.html";
    }
}