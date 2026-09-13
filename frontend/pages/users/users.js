requireAuth();

let allUsers = [];


/* =========================
   DOM ELEMENTS
========================= */

const usersTableBody =
    document.getElementById("usersTableBody");

const loadingState =
    document.getElementById("loadingState");

const emptyState =
    document.getElementById("emptyState");

const tableContainer =
    document.getElementById("tableContainer");

const errorMessage =
    document.getElementById("errorMessage");

const searchInput =
    document.getElementById("searchInput");

const roleFilter =
    document.getElementById("roleFilter");

const refreshButton =
    document.getElementById("refreshButton");

const logoutButton =
    document.getElementById("logoutButton");

const totalUsers =
    document.getElementById("totalUsers");

const totalAdmins =
    document.getElementById("totalAdmins");

const totalCustomers =
    document.getElementById("totalCustomers");

const topbarUserEmail =
    document.getElementById("topbarUserEmail");

const topbarUserRole =
    document.getElementById("topbarUserRole");


/* MODAL */

const userModal =
    document.getElementById("userModal");

const closeModalButton =
    document.getElementById("closeModalButton");

const closeModalFooter =
    document.getElementById("closeModalFooter");

const detailUserId =
    document.getElementById("detailUserId");

const detailEmail =
    document.getElementById("detailEmail");

const detailRole =
    document.getElementById("detailRole");

const detailCreated =
    document.getElementById("detailCreated");


/* =========================
   INITIALIZATION
========================= */

document.addEventListener(
    "DOMContentLoaded",
    initializePage
);


async function initializePage() {

    const currentUser =
        getStoredUser();

    if (
        currentUser &&
        currentUser.role !== "admin"
    ) {

        showError(
            "Access denied. Only administrators can view users."
        );

        return;
    }

    setupUserHeader(currentUser);

    setupEventListeners();

    await loadUsers();
}


/* =========================
   HEADER
========================= */

function setupUserHeader(user) {

    if (!user) {
        return;
    }

    topbarUserEmail.textContent =
        user.email;

    topbarUserRole.textContent =
        formatRole(user.role);
}


/* =========================
   EVENT LISTENERS
========================= */

function setupEventListeners() {

    refreshButton.addEventListener(
        "click",
        loadUsers
    );


    searchInput.addEventListener(
        "input",
        applyFilters
    );


    roleFilter.addEventListener(
        "change",
        applyFilters
    );


    closeModalButton.addEventListener(
        "click",
        closeModal
    );


    closeModalFooter.addEventListener(
        "click",
        closeModal
    );


    userModal.addEventListener(
        "click",
        function (event) {

            if (
                event.target === userModal
            ) {
                closeModal();
            }

        }
    );


    logoutButton.addEventListener(
        "click",
        logout
    );


    const notificationsNav =
        document.getElementById("notificationsNav");

    if (notificationsNav) {
        notificationsNav.href =
            "../notifications/notifications.html";
    }
}


/* =========================
   LOAD USERS
========================= */

async function loadUsers() {

    showLoading();

    try {

        const users =
            await getUsers();

        allUsers =
            Array.isArray(users)
                ? users
                : [];

        updateSummary();

        applyFilters();

    } catch (error) {

        showError(
            error.message ||
            "Unable to load users."
        );

    }
}


/* =========================
   SUMMARY
========================= */

function updateSummary() {

    const admins =
        allUsers.filter(
            user => user.role === "admin"
        ).length;

    const customers =
        allUsers.filter(
            user => user.role === "customer"
        ).length;

    totalUsers.textContent =
        allUsers.length;

    totalAdmins.textContent =
        admins;

    totalCustomers.textContent =
        customers;
}


/* =========================
   FILTERS
========================= */

function applyFilters() {

    const searchTerm =
        searchInput.value
            .trim()
            .toLowerCase();

    const selectedRole =
        roleFilter.value;

    const filteredUsers =
        allUsers.filter(function (user) {

            const email =
                String(user.email || "")
                    .toLowerCase();

            const matchesSearch =
                email.includes(searchTerm);

            const matchesRole =
                selectedRole === "all" ||
                user.role === selectedRole;

            return (
                matchesSearch &&
                matchesRole
            );

        });


    renderUsers(filteredUsers);
}


/* =========================
   RENDER USERS
========================= */

function renderUsers(users) {

    hideAllStates();

    if (!users.length) {

        emptyState.classList.remove(
            "hidden"
        );

        return;
    }


    tableContainer.classList.remove(
        "hidden"
    );


    usersTableBody.innerHTML = "";


    users.forEach(function (user) {

        const row =
            document.createElement("tr");


        const createdDate =
            formatDate(user.created_at);


        const roleClass =
            user.role === "admin"
                ? "role-admin"
                : "role-customer";


        const roleText =
            formatRole(user.role);


        row.innerHTML = `
            <td class="user-id">
                #${user.id}
            </td>

            <td class="user-email">
                ${escapeHtml(user.email)}
            </td>

            <td>
                <span class="role-badge ${roleClass}">
                    ${roleText}
                </span>
            </td>

            <td>
                ${createdDate}
            </td>

            <td>
                <button
                    class="view-button"
                    data-user-id="${user.id}"
                >
                    View
                </button>
            </td>
        `;


        const viewButton =
            row.querySelector(".view-button");


        viewButton.addEventListener(
            "click",
            function () {

                openUserDetails(user.id);

            }
        );


        usersTableBody.appendChild(row);

    });
}


/* =========================
   USER DETAILS
========================= */

async function openUserDetails(userId) {

    try {

        const user =
            await getUser(userId);

        detailUserId.textContent =
            `#${user.id}`;

        detailEmail.textContent =
            user.email;

        detailRole.textContent =
            formatRole(user.role);

        detailCreated.textContent =
            formatDate(user.created_at);

        userModal.classList.remove(
            "hidden"
        );

    } catch (error) {

        showError(
            error.message ||
            "Unable to load user details."
        );

    }
}


function closeModal() {

    userModal.classList.add(
        "hidden"
    );
}


/* =========================
   PAGE STATES
========================= */

function showLoading() {

    hideAllStates();

    loadingState.classList.remove(
        "hidden"
    );
}


function showError(message) {

    hideAllStates();

    errorMessage.textContent =
        message;

    errorMessage.classList.remove(
        "hidden"
    );
}


function hideAllStates() {

    loadingState.classList.add(
        "hidden"
    );

    emptyState.classList.add(
        "hidden"
    );

    tableContainer.classList.add(
        "hidden"
    );

    errorMessage.classList.add(
        "hidden"
    );
}


/* =========================
   HELPERS
========================= */

function formatRole(role) {

    if (role === "admin") {
        return "Administrator";
    }

    if (role === "customer") {
        return "Customer";
    }

    return role || "Unknown";
}


function formatDate(dateString) {

    if (!dateString) {
        return "-";
    }

    const date =
        new Date(dateString);

    if (Number.isNaN(date.getTime())) {
        return "-";
    }

    return date.toLocaleDateString(
        "en-IN",
        {
            day: "2-digit",
            month: "short",
            year: "numeric"
        }
    );
}


function escapeHtml(value) {

    const div =
        document.createElement("div");

    div.textContent =
        value ?? "";

    return div.innerHTML;
}