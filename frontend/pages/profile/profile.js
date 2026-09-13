/* ============================================================
   AUTHENTICATION
   ============================================================ */

requireAuth();


/* ============================================================
   DOM ELEMENTS
   ============================================================ */

const userEmail =
    document.getElementById("userEmail");

const userRole =
    document.getElementById("userRole");

const userAvatar =
    document.getElementById("userAvatar");

const largeAvatar =
    document.getElementById("largeAvatar");

const profileEmail =
    document.getElementById("profileEmail");

const profileRole =
    document.getElementById("profileRole");

const profileId =
    document.getElementById("profileId");

const profileEmailValue =
    document.getElementById(
        "profileEmailValue"
    );

const profileRoleValue =
    document.getElementById(
        "profileRoleValue"
    );

const profileCreatedAt =
    document.getElementById(
        "profileCreatedAt"
    );

const securityRole =
    document.getElementById(
        "securityRole"
    );

const errorMessage =
    document.getElementById(
        "errorMessage"
    );

const logoutButton =
    document.getElementById(
        "logoutButton"
    );


/* ============================================================
   INITIALIZATION
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    initializeProfile
);


async function initializeProfile() {

    loadStoredUser();

    setupNavigation();

    setupLogout();

    await loadProfile();
}


/* ============================================================
   STORED USER
   ============================================================ */

function loadStoredUser() {

    const user =
        getStoredUser();


    if (!user) {
        return;
    }


    const email =
        user.email || "User";


    const role =
        user.role || "customer";


    const initial =
        email
            .charAt(0)
            .toUpperCase();


    userEmail.textContent =
        email;


    userRole.textContent =
        role;


    userAvatar.textContent =
        initial;


    largeAvatar.textContent =
        initial;


    profileEmail.textContent =
        email;


    profileRole.textContent =
        role;


    profileRoleValue.textContent =
        role;


    securityRole.textContent =
        role;
}


/* ============================================================
   LOAD PROFILE
   ============================================================ */

async function loadProfile() {

    hideError();


    try {

        const user =
            await getCurrentUser();


        displayProfile(
            user
        );


        localStorage.setItem(
            "current_user",
            JSON.stringify(user)
        );


    } catch (error) {

        console.error(
            "Profile loading error:",
            error
        );


        showError(
            error.message ||
            "Unable to load profile information."
        );
    }
}


/* ============================================================
   DISPLAY PROFILE
   ============================================================ */

function displayProfile(
    user
) {

    if (!user) {
        return;
    }


    const email =
        user.email || "User";


    const role =
        user.role || "customer";


    const initial =
        email
            .charAt(0)
            .toUpperCase();


    userEmail.textContent =
        email;


    userRole.textContent =
        role;


    userAvatar.textContent =
        initial;


    largeAvatar.textContent =
        initial;


    profileEmail.textContent =
        email;


    profileRole.textContent =
        role;


    profileId.textContent =
        user.id ?? "—";


    profileEmailValue.textContent =
        email;


    profileRoleValue.textContent =
        role;


    profileCreatedAt.textContent =
        formatDateTime(
            user.created_at
        );


    securityRole.textContent =
        role;
}


/* ============================================================
   DATE FORMATTING
   ============================================================ */

function formatDateTime(
    dateString
) {

    if (!dateString) {
        return "—";
    }


    const date =
        new Date(dateString);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return "—";
    }


    return date.toLocaleString(
        undefined,
        {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        }
    );
}


/* ============================================================
   NAVIGATION
   ============================================================ */

function setupNavigation() {

    const navigationTargets = {
        notificationsNav:
            "/frontend/pages/notifications/notifications.html",
        eventsNav:
            "/frontend/pages/events/events.html",
        usersNav:
            "/frontend/pages/users/users.html"
    };


    Object.entries(navigationTargets).forEach(
        ([elementId, target]) => {

            const element =
                document.getElementById(
                    elementId
                );


            if (!element) {
                return;
            }


            element.addEventListener(
                "click",
                event => {

                    event.preventDefault();

                    window.location.href = target;

                }
            );

        }
    );
}


/* ============================================================
   LOGOUT
   ============================================================ */

function setupLogout() {

    logoutButton.addEventListener(
        "click",
        () => {

            logout();

        }
    );
}


/* ============================================================
   ERROR
   ============================================================ */

function showError(
    message
) {

    errorMessage.textContent =
        message;


    errorMessage.classList.remove(
        "hidden"
    );
}


function hideError() {

    errorMessage.classList.add(
        "hidden"
    );
}