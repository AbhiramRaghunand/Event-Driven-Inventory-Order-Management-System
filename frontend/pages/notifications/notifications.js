requireAuth();


let notifications = [];


/* ================================
   INITIALIZATION
================================ */

document.addEventListener("DOMContentLoaded", () => {

    setupUserInfo();
    setupNavigation();
    setupActions();

    loadNotifications();

});


/* ================================
   USER INFO
================================ */

function setupUserInfo() {

    const user = getStoredUser();

    if (!user) {
        return;
    }

    const emailElement =
        document.getElementById("userEmail");

    const roleElement =
        document.getElementById("userRole");

    const avatarElement =
        document.getElementById("userAvatar");

    if (emailElement) {
        emailElement.textContent =
            user.email || "User";
    }

    if (roleElement) {
        roleElement.textContent =
            user.role
                ? capitalize(user.role)
                : "User";
    }

    if (avatarElement) {

        avatarElement.textContent =
            user.email
                ? user.email.charAt(0).toUpperCase()
                : "U";
    }

    /*
     * Hide administration navigation
     * for customers.
     */

    if (user.role !== "admin") {

        const adminNavigation =
            document.getElementById(
                "adminNavigation"
            );

        if (adminNavigation) {
            adminNavigation.classList.add("hidden");
        }
    }
}


/* ================================
   NAVIGATION
================================ */

function setupNavigation() {

    const logoutButton =
        document.getElementById("logoutButton");

    if (logoutButton) {

        logoutButton.addEventListener(
            "click",
            () => {
                logout();
            }
        );
    }
}


/* ================================
   ACTIONS
================================ */

function setupActions() {

    const refreshButton =
        document.getElementById("refreshButton");

    const markAllButton =
        document.getElementById("markAllButton");

    const retryButton =
        document.getElementById("retryButton");


    if (refreshButton) {

        refreshButton.addEventListener(
            "click",
            loadNotifications
        );
    }


    if (markAllButton) {

        markAllButton.addEventListener(
            "click",
            markAllAsRead
        );
    }


    if (retryButton) {

        retryButton.addEventListener(
            "click",
            loadNotifications
        );
    }
}


/* ================================
   LOAD NOTIFICATIONS
================================ */

async function loadNotifications() {

    showLoading();
    hideStatus();

    try {

        const response =
            await getNotifications();

        notifications =
            Array.isArray(response)
                ? response
                : [];

        notifications.sort(
            (a, b) =>
                new Date(b.created_at) -
                new Date(a.created_at)
        );

        updateSummary();

        renderNotifications();

    } catch (error) {

        console.error(
            "Failed to load notifications:",
            error
        );

        showError(
            error.message ||
            "Unable to load notifications."
        );
    }
}


/* ================================
   SUMMARY
================================ */

function updateSummary() {

    const total =
        notifications.length;

    const unread =
        notifications.filter(
            notification =>
                !notification.is_read
        ).length;

    const orderNotifications =
        notifications.filter(
            notification =>
                notification.event_type ===
                    "ORDER_CREATED" ||
                notification.event_type ===
                    "ORDER_CANCELLED"
        ).length;

    const lowStockNotifications =
        notifications.filter(
            notification =>
                notification.event_type ===
                "LOW_STOCK"
        ).length;


    document.getElementById(
        "totalNotifications"
    ).textContent = total;

    document.getElementById(
        "unreadNotifications"
    ).textContent = unread;

    document.getElementById(
        "orderNotifications"
    ).textContent = orderNotifications;

    document.getElementById(
        "lowStockNotifications"
    ).textContent = lowStockNotifications;


    const markAllButton =
        document.getElementById(
            "markAllButton"
        );

    if (markAllButton) {

        markAllButton.disabled =
            unread === 0;
    }
}


/* ================================
   RENDER
================================ */

function renderNotifications() {

    const list =
        document.getElementById(
            "notificationsList"
        );

    const emptyState =
        document.getElementById(
            "emptyState"
        );

    const loadingState =
        document.getElementById(
            "loadingState"
        );

    const errorState =
        document.getElementById(
            "errorState"
        );


    loadingState.classList.add("hidden");
    errorState.classList.add("hidden");


    if (notifications.length === 0) {

        list.classList.add("hidden");
        emptyState.classList.remove("hidden");

        return;
    }


    emptyState.classList.add("hidden");
    list.classList.remove("hidden");


    list.innerHTML =
        notifications
            .map(
                notification =>
                    createNotificationHTML(
                        notification
                    )
            )
            .join("");


    attachNotificationActions();
}


/* ================================
   NOTIFICATION HTML
================================ */

function createNotificationHTML(
    notification
) {

    const unreadClass =
        notification.is_read
            ? ""
            : "unread";

    const type =
        formatEventType(
            notification.event_type
        );

    const message =
        escapeHTML(
            notification.message ||
            "No message available."
        );

    const timestamp =
        formatDate(
            notification.created_at
        );


    return `
        <div
            class="notification-item ${unreadClass}"
            data-id="${notification.id}"
        >

            <div class="notification-main">

                <div class="notification-indicator"></div>

                <div class="notification-content">

                    <div class="notification-top">

                        <span class="notification-type">
                            ${type}
                        </span>

                    </div>

                    <div class="notification-message">
                        ${message}
                    </div>

                    <div class="notification-time">
                        ${timestamp}
                    </div>

                </div>

            </div>


            <div class="notification-actions">

                ${
                    notification.is_read
                        ? `
                            <span class="read-label">
                                Read
                            </span>
                        `
                        : `
                            <button
                                type="button"
                                class="mark-read-button"
                                data-id="${notification.id}"
                            >
                                Mark as read
                            </button>
                        `
                }

            </div>

        </div>
    `;
}


/* ================================
   INDIVIDUAL MARK AS READ
================================ */

function attachNotificationActions() {

    const buttons =
        document.querySelectorAll(
            ".mark-read-button"
        );


    buttons.forEach(button => {

        button.addEventListener(
            "click",
            async () => {

                const notificationId =
                    button.dataset.id;

                await markAsRead(
                    notificationId,
                    button
                );
            }
        );

    });
}


async function markAsRead(
    notificationId,
    button
) {

    button.disabled = true;
    button.textContent = "Updating...";


    try {

        await markNotificationAsRead(
            notificationId
        );


        const notification =
            notifications.find(
                item =>
                    String(item.id) ===
                    String(notificationId)
            );


        if (notification) {
            notification.is_read = true;
        }


        updateSummary();
        renderNotifications();


        showStatus(
            "Notification marked as read.",
            "success"
        );


    } catch (error) {

        console.error(
            "Failed to mark notification as read:",
            error
        );


        button.disabled = false;
        button.textContent = "Mark as read";


        showStatus(
            error.message ||
            "Unable to update notification.",
            "error"
        );
    }
}


/* ================================
   MARK ALL AS READ
================================ */

async function markAllAsRead() {

    const markAllButton =
        document.getElementById(
            "markAllButton"
        );


    markAllButton.disabled = true;
    markAllButton.textContent =
        "Updating...";


    try {

        await markAllNotificationsAsRead();


        notifications.forEach(
            notification => {
                notification.is_read = true;
            }
        );


        updateSummary();
        renderNotifications();


        showStatus(
            "All notifications marked as read.",
            "success"
        );


    } catch (error) {

        console.error(
            "Failed to mark all notifications:",
            error
        );


        showStatus(
            error.message ||
            "Unable to update notifications.",
            "error"
        );


        markAllButton.disabled = false;
        markAllButton.textContent =
            "Mark all as read";

        return;
    }


    markAllButton.textContent =
        "Mark all as read";
}


/* ================================
   STATES
================================ */

function showLoading() {

    document
        .getElementById("loadingState")
        .classList.remove("hidden");

    document
        .getElementById("emptyState")
        .classList.add("hidden");

    document
        .getElementById("errorState")
        .classList.add("hidden");

    document
        .getElementById("notificationsList")
        .classList.add("hidden");
}


function showError(message) {

    document
        .getElementById("loadingState")
        .classList.add("hidden");

    document
        .getElementById("emptyState")
        .classList.add("hidden");

    document
        .getElementById("notificationsList")
        .classList.add("hidden");

    document
        .getElementById("errorState")
        .classList.remove("hidden");

    document
        .getElementById("errorText")
        .textContent = message;
}


/* ================================
   STATUS MESSAGE
================================ */

function showStatus(
    message,
    type
) {

    const status =
        document.getElementById(
            "statusMessage"
        );

    status.textContent = message;

    status.className =
        type === "success"
            ? "status-success"
            : "status-error";

    setTimeout(() => {
        hideStatus();
    }, 3000);
}


function hideStatus() {

    const status =
        document.getElementById(
            "statusMessage"
        );

    status.className = "hidden";
    status.textContent = "";
}


/* ================================
   FORMATTING
================================ */

function formatEventType(
    eventType
) {

    if (!eventType) {
        return "System";
    }

    return eventType
        .replace(/_/g, " ")
        .toLowerCase()
        .replace(/\b\w/g, letter =>
            letter.toUpperCase()
        );
}


function formatDate(
    dateString
) {

    if (!dateString) {
        return "Unknown time";
    }

    const date =
        new Date(dateString);

    if (Number.isNaN(date.getTime())) {
        return dateString;
    }

    return date.toLocaleString(
        undefined,
        {
            dateStyle: "medium",
            timeStyle: "short"
        }
    );
}


function capitalize(value) {

    if (!value) {
        return "";
    }

    return value.charAt(0).toUpperCase() +
        value.slice(1);
}


/* ================================
   HTML ESCAPING
================================ */

function escapeHTML(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}