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

const adminNavigation =
    document.getElementById(
        "adminNavigation"
    );

const logoutButton =
    document.getElementById(
        "logoutButton"
    );

const refreshButton =
    document.getElementById(
        "refreshButton"
    );

const notificationsNav =
    document.getElementById(
        "notificationsNav"
    );

const loadingState =
    document.getElementById(
        "loadingState"
    );

const tableContainer =
    document.getElementById(
        "tableContainer"
    );

const eventsTableBody =
    document.getElementById(
        "eventsTableBody"
    );

const emptyState =
    document.getElementById(
        "emptyState"
    );

const errorMessage =
    document.getElementById(
        "errorMessage"
    );

const eventCount =
    document.getElementById(
        "eventCount"
    );

const orderCreatedCount =
    document.getElementById(
        "orderCreatedCount"
    );

const orderCancelledCount =
    document.getElementById(
        "orderCancelledCount"
    );

const lowStockCount =
    document.getElementById(
        "lowStockCount"
    );


/* ============================================================
   DETAILS MODAL
   ============================================================ */

const eventDetailsModal =
    document.getElementById(
        "eventDetailsModal"
    );

const closeDetailsModalButton =
    document.getElementById(
        "closeDetailsModalButton"
    );

const closeDetailsButton =
    document.getElementById(
        "closeDetailsButton"
    );

const detailsEventType =
    document.getElementById(
        "detailsEventType"
    );

const detailsEventId =
    document.getElementById(
        "detailsEventId"
    );

const detailsDatabaseId =
    document.getElementById(
        "detailsDatabaseId"
    );

const detailsTypeValue =
    document.getElementById(
        "detailsTypeValue"
    );

const detailsEventIdValue =
    document.getElementById(
        "detailsEventIdValue"
    );

const detailsProcessedAt =
    document.getElementById(
        "detailsProcessedAt"
    );

const detailsEventData =
    document.getElementById(
        "detailsEventData"
    );


/* ============================================================
   STATE
   ============================================================ */

let currentEvents = [];


/* ============================================================
   INITIALIZATION
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    initializeEventsPage
);


async function initializeEventsPage() {

    loadUserInformation();

    setupNavigation();

    setupLogout();

    setupModalEvents();

    await loadEvents();

}


/* ============================================================
   USER INFORMATION
   ============================================================ */

function loadUserInformation() {

    const user =
        getStoredUser();


    if (!user) {
        return;
    }


    userEmail.textContent =
        user.email || "User";


    userRole.textContent =
        user.role || "admin";


    userAvatar.textContent =
        (user.email || "U")
            .charAt(0)
            .toUpperCase();


    const role =
        String(user.role || "")
            .toLowerCase();


    if (role !== "admin") {

        adminNavigation.classList.add(
            "hidden"
        );

    }

}


/* ============================================================
   LOAD EVENTS
   ============================================================ */

async function loadEvents() {

    showLoadingState();

    hideError();


    try {

        const events =
            await getEvents();


        currentEvents =
            Array.isArray(events)
                ? events
                : [];


        sortEvents();

        updateSummary();

        renderEvents();


    } catch (error) {

        console.error(
            "Events loading error:",
            error
        );


        showError(
            error.message ||
            "Unable to load events."
        );


        showEmptyState(
            "Unable to load events."
        );

    } finally {

        loadingState.classList.add(
            "hidden"
        );

    }

}


/* ============================================================
   SORT EVENTS
   ============================================================ */

function sortEvents() {

    currentEvents.sort(
        (a, b) =>
            new Date(
                b.processed_at
            ) -
            new Date(
                a.processed_at
            )
    );

}


/* ============================================================
   SUMMARY
   ============================================================ */

function updateSummary() {

    eventCount.textContent =
        currentEvents.length;


    orderCreatedCount.textContent =
        countEventType(
            "ORDER_CREATED"
        );


    orderCancelledCount.textContent =
        countEventType(
            "ORDER_CANCELLED"
        );


    lowStockCount.textContent =
        countEventType(
            "LOW_STOCK"
        );

}


function countEventType(
    eventType
) {

    return currentEvents.filter(
        event =>
            normalizeEventType(
                event.event_type
            ) === eventType
    ).length;

}


/* ============================================================
   RENDER EVENTS
   ============================================================ */

function renderEvents() {

    eventsTableBody.innerHTML = "";


    if (currentEvents.length === 0) {

        showEmptyState(
            "No events found."
        );

        return;
    }


    emptyState.classList.add(
        "hidden"
    );


    tableContainer.classList.remove(
        "hidden"
    );


    currentEvents.forEach(
        event => {

            const row =
                document.createElement(
                    "tr"
                );


            const eventType =
                normalizeEventType(
                    event.event_type
                );


            const preview =
                createEventPreview(
                    event.event_data
                );


            row.innerHTML =
                `
                <td>

                    <span
                        class="event-id"
                        title="${escapeHtml(
                            event.event_id
                        )}"
                    >
                        ${escapeHtml(
                            event.event_id
                        )}
                    </span>

                </td>


                <td>

                    <span class="event-type">
                        ${escapeHtml(
                            eventType
                        )}
                    </span>

                </td>


                <td>

                    <span
                        class="event-data-preview"
                        title="${escapeHtml(
                            preview
                        )}"
                    >
                        ${escapeHtml(
                            preview
                        )}
                    </span>

                </td>


                <td>

                    <span class="event-date">
                        ${formatDateTime(
                            event.processed_at
                        )}
                    </span>

                </td>


                <td>

                    <button
                        type="button"
                        class="action-button"
                        data-action="view"
                        data-event-id="${escapeHtml(
                            event.event_id
                        )}"
                    >
                        View
                    </button>

                </td>
                `;


            eventsTableBody.appendChild(
                row
            );

        }
    );

}


/* ============================================================
   EVENT DETAILS
   ============================================================ */

function openEventDetails(
    event
) {

    detailsEventType.textContent =
        normalizeEventType(
            event.event_type
        );


    detailsEventId.textContent =
        event.event_id || "—";


    detailsDatabaseId.textContent =
        event.id ?? "—";


    detailsTypeValue.textContent =
        normalizeEventType(
            event.event_type
        );


    detailsEventIdValue.textContent =
        event.event_id || "—";


    detailsProcessedAt.textContent =
        formatDateTime(
            event.processed_at
        );


    detailsEventData.textContent =
        JSON.stringify(
            event.event_data ?? {},
            null,
            2
        );


    eventDetailsModal.classList.remove(
        "hidden"
    );

}


function closeEventDetails() {

    eventDetailsModal.classList.add(
        "hidden"
    );

}


/* ============================================================
   TABLE ACTIONS
   ============================================================ */

eventsTableBody.addEventListener(
    "click",
    event => {

        const button =
            event.target.closest(
                "[data-action]"
            );


        if (!button) {
            return;
        }


        const eventId =
            button.dataset.eventId;


        if (!eventId) {
            return;
        }


        const selectedEvent =
            currentEvents.find(
                item =>
                    item.event_id === eventId
            );


        if (!selectedEvent) {
            return;
        }


        if (
            button.dataset.action ===
            "view"
        ) {

            openEventDetails(
                selectedEvent
            );

        }

    }
);


/* ============================================================
   MODAL EVENTS
   ============================================================ */

function setupModalEvents() {

    closeDetailsModalButton.addEventListener(
        "click",
        closeEventDetails
    );


    closeDetailsButton.addEventListener(
        "click",
        closeEventDetails
    );


    eventDetailsModal.addEventListener(
        "click",
        event => {

            if (
                event.target ===
                eventDetailsModal
            ) {

                closeEventDetails();

            }

        }
    );


    document.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Escape" &&
                !eventDetailsModal.classList.contains(
                    "hidden"
                )
            ) {

                closeEventDetails();

            }

        }
    );

}


/* ============================================================
   NAVIGATION
   ============================================================ */

function setupNavigation() {

    if (!notificationsNav) {
        return;
    }


    notificationsNav.addEventListener(
        "click",
        event => {

            window.location.href =
                    "/notifications";


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
   STATES
   ============================================================ */

function showLoadingState() {

    loadingState.classList.remove(
        "hidden"
    );


    tableContainer.classList.add(
        "hidden"
    );


    emptyState.classList.add(
        "hidden"
    );

}


function showEmptyState(
    message
) {

    loadingState.classList.add(
        "hidden"
    );


    tableContainer.classList.add(
        "hidden"
    );


    emptyState.classList.remove(
        "hidden"
    );


    const paragraph =
        emptyState.querySelector(
            "p"
        );


    if (paragraph) {

        paragraph.textContent =
            message;

    }

}


/* ============================================================
   ERROR
   ============================================================ */

function hideError() {

    errorMessage.classList.add(
        "hidden"
    );

}


function showError(
    message
) {

    errorMessage.textContent =
        message;


    errorMessage.classList.remove(
        "hidden"
    );

}


/* ============================================================
   EVENT HELPERS
   ============================================================ */

function normalizeEventType(
    eventType
) {

    return String(
        eventType || ""
    )
        .trim()
        .toUpperCase();

}


function createEventPreview(
    eventData
) {

    if (
        eventData === null ||
        eventData === undefined
    ) {

        return "No event data";

    }


    try {

        return JSON.stringify(
            eventData
        );

    } catch (error) {

        return "Unable to display event data";

    }

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
        new Date(
            dateString
        );


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
   HTML ESCAPING
   ============================================================ */

function escapeHtml(
    value
) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        String(
            value ?? ""
        );


    return div.innerHTML;

}


/* ============================================================
   REFRESH
   ============================================================ */

refreshButton.addEventListener(
    "click",
    loadEvents
);