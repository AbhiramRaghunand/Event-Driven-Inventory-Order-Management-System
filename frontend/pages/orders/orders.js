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
    document.getElementById("adminNavigation");

const ordersDescription =
    document.getElementById(
        "ordersDescription"
    );

const logoutButton =
    document.getElementById("logoutButton");

const refreshButton =
    document.getElementById("refreshButton");

const loadingState =
    document.getElementById("loadingState");

const tableContainer =
    document.getElementById(
        "tableContainer"
    );

const ordersTableBody =
    document.getElementById(
        "ordersTableBody"
    );

const emptyState =
    document.getElementById("emptyState");

const errorMessage =
    document.getElementById("errorMessage");

const successMessage =
    document.getElementById(
        "successMessage"
    );

const orderCount =
    document.getElementById("orderCount");

const confirmedCount =
    document.getElementById(
        "confirmedCount"
    );

const cancelledCount =
    document.getElementById(
        "cancelledCount"
    );

const customerHeader =
    document.getElementById(
        "customerHeader"
    );


/* ============================================================
   DETAILS MODAL
   ============================================================ */

const orderDetailsModal =
    document.getElementById(
        "orderDetailsModal"
    );

const closeDetailsModalButton =
    document.getElementById(
        "closeDetailsModalButton"
    );

const closeDetailsButton =
    document.getElementById(
        "closeDetailsButton"
    );

const detailsOrderId =
    document.getElementById(
        "detailsOrderId"
    );

const detailsOrderIdValue =
    document.getElementById(
        "detailsOrderIdValue"
    );

const detailsUserId =
    document.getElementById(
        "detailsUserId"
    );

const detailsStatus =
    document.getElementById(
        "detailsStatus"
    );

const detailsCreatedAt =
    document.getElementById(
        "detailsCreatedAt"
    );

const detailsItemsCount =
    document.getElementById(
        "detailsItemsCount"
    );

const detailsItemsList =
    document.getElementById(
        "detailsItemsList"
    );


/* ============================================================
   CANCEL MODAL
   ============================================================ */

const cancelOrderModal =
    document.getElementById(
        "cancelOrderModal"
    );

const closeCancelModalButton =
    document.getElementById(
        "closeCancelModalButton"
    );

const cancelOrderCancelButton =
    document.getElementById(
        "cancelOrderCancelButton"
    );

const confirmCancelButton =
    document.getElementById(
        "confirmCancelButton"
    );

const cancelOrderName =
    document.getElementById(
        "cancelOrderName"
    );


/* ============================================================
   STATE
   ============================================================ */

let currentOrders = [];

let orderPendingCancellation = null;


/* ============================================================
   PAGE INITIALIZATION
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    initializeOrdersPage
);


async function initializeOrdersPage() {

    loadUserInformation();

    setupNavigation();

    setupLogout();

    setupModalEvents();

    await loadOrders();
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
        user.role || "customer";


    userAvatar.textContent =
        (user.email || "U")
            .charAt(0)
            .toUpperCase();


    const role =
        String(user.role || "")
            .toLowerCase();


    if (role === "admin") {

        adminNavigation.classList.remove(
            "hidden"
        );

        ordersDescription.textContent =
            "All orders currently recorded in the system.";

        customerHeader.classList.remove(
            "hidden"
        );

    } else {

        adminNavigation.classList.add(
            "hidden"
        );

        ordersDescription.textContent =
            "Orders associated with your account.";

    }
}


/* ============================================================
   ROLE
   ============================================================ */

function isAdmin() {

    const user =
        getStoredUser();


    return (
        user &&
        String(user.role || "")
            .toLowerCase() === "admin"
    );
}


/* ============================================================
   LOAD ORDERS
   ============================================================ */

async function loadOrders() {

    showLoadingState();

    hideMessages();


    try {

        const orders =
            await getOrders();


        currentOrders =
            Array.isArray(orders)
                ? orders
                : [];


        sortOrders();


        updateSummary();

        renderOrders();


    } catch (error) {

        console.error(
            "Orders loading error:",
            error
        );


        showPageError(
            error.message ||
            "Unable to load orders."
        );


        showEmptyState(
            "Unable to load orders."
        );

    } finally {

        loadingState.classList.add(
            "hidden"
        );
    }
}


/* ============================================================
   SORT ORDERS
   ============================================================ */

function sortOrders() {

    currentOrders.sort(
        (a, b) =>
            new Date(b.created_at) -
            new Date(a.created_at)
    );
}


/* ============================================================
   SUMMARY
   ============================================================ */

function updateSummary() {

    const confirmedOrders =
        currentOrders.filter(
            order =>
                normalizeStatus(
                    order.status
                ) === "confirmed"
        );


    const cancelledOrders =
        currentOrders.filter(
            order =>
                normalizeStatus(
                    order.status
                ) === "cancelled"
        );


    orderCount.textContent =
        currentOrders.length;


    confirmedCount.textContent =
        confirmedOrders.length;


    cancelledCount.textContent =
        cancelledOrders.length;
}


/* ============================================================
   RENDER ORDERS
   ============================================================ */

function renderOrders() {

    ordersTableBody.innerHTML = "";


    if (currentOrders.length === 0) {

        showEmptyState(
            "No orders found."
        );

        return;
    }


    emptyState.classList.add(
        "hidden"
    );

    tableContainer.classList.remove(
        "hidden"
    );


    currentOrders.forEach(
        order => {

            const row =
                document.createElement(
                    "tr"
                );


            const status =
                normalizeStatus(
                    order.status
                );


            const itemCount =
                Array.isArray(
                    order.items
                )
                    ? order.items.length
                    : 0;


            const cancelButton =
                status === "confirmed"
                    ? `
                        <button
                            type="button"
                            class="action-button cancel-action-button"
                            data-action="cancel"
                            data-order-id="${order.id}"
                        >
                            Cancel
                        </button>
                    `
                    : "";


            const customerCell =
                isAdmin()
                    ? `
                        <td>
                            <span class="customer-id">
                                User #${order.user_id}
                            </span>
                        </td>
                    `
                    : "";


            row.innerHTML =
                `
                <td>

                    <span class="order-id">
                        #${order.id}
                    </span>

                </td>


                ${customerCell}


                <td>

                    <span class="items-count-cell">
                        ${itemCount}
                        ${itemCount === 1 ? "item" : "items"}
                    </span>

                </td>


                <td>

                    ${getStatusBadge(
                        status
                    )}

                </td>


                <td>

                    <span class="order-date">
                        ${formatDate(
                            order.created_at
                        )}
                    </span>

                </td>


                <td class="actions-cell">

                    <button
                        type="button"
                        class="action-button"
                        data-action="view"
                        data-order-id="${order.id}"
                    >
                        View
                    </button>

                    ${cancelButton}

                </td>
                `;


            ordersTableBody.appendChild(
                row
            );

        }
    );
}


/* ============================================================
   STATUS
   ============================================================ */

function normalizeStatus(
    status
) {

    return String(
        status || ""
    )
        .toLowerCase();
}


function getStatusBadge(
    status
) {

    const normalizedStatus =
        normalizeStatus(status);


    let className =
        "status-badge";


    if (
        normalizedStatus ===
        "confirmed"
    ) {

        className +=
            " status-confirmed";

    } else if (
        normalizedStatus ===
        "cancelled"
    ) {

        className +=
            " status-cancelled";
    }


    const displayStatus =
        normalizedStatus ||
        "unknown";


    return `
        <span class="${className}">
            ${escapeHtml(
                displayStatus
            )}
        </span>
    `;
}


/* ============================================================
   VIEW ORDER DETAILS
   ============================================================ */

function openOrderDetails(
    order
) {

    detailsOrderId.textContent =
        `#${order.id}`;


    detailsOrderIdValue.textContent =
        `#${order.id}`;


    detailsUserId.textContent =
        `#${order.user_id}`;


    detailsStatus.innerHTML =
        getStatusBadge(
            order.status
        );


    detailsCreatedAt.textContent =
        formatDateTime(
            order.created_at
        );


    const items =
        Array.isArray(order.items)
            ? order.items
            : [];


    detailsItemsCount.textContent =
        items.length;


    renderOrderItems(
        items
    );


    orderDetailsModal.classList.remove(
        "hidden"
    );
}


function renderOrderItems(
    items
) {

    detailsItemsList.innerHTML = "";


    if (items.length === 0) {

        detailsItemsList.innerHTML =
            `
            <div class="details-empty">
                No items found for this order.
            </div>
            `;

        return;
    }


    items.forEach(
        (item, index) => {

            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "detail-product-row";


            row.innerHTML =
                `
                <div class="detail-product-info">

                    <div class="detail-product-icon">
                        ${index + 1}
                    </div>

                    <div>

                        <div class="detail-product-name">
                            Product #${item.product_id}
                        </div>

                        <div class="detail-product-id">
                            Product ID: ${item.product_id}
                        </div>

                    </div>

                </div>


                <div class="detail-product-quantity">
                    Quantity: ${item.quantity}
                </div>
                `;


            detailsItemsList.appendChild(
                row
            );

        }
    );
}


function closeOrderDetails() {

    orderDetailsModal.classList.add(
        "hidden"
    );
}


/* ============================================================
   CANCEL ORDER MODAL
   ============================================================ */

function openCancelOrderModal(
    order
) {

    orderPendingCancellation =
        order;


    cancelOrderName.textContent =
        `Order #${order.id}`;


    cancelOrderModal.classList.remove(
        "hidden"
    );
}


function closeCancelOrderModal() {

    cancelOrderModal.classList.add(
        "hidden"
    );


    orderPendingCancellation =
        null;
}


/* ============================================================
   CANCEL ORDER
   ============================================================ */

async function confirmOrderCancellation() {

    if (
        !orderPendingCancellation
    ) {
        return;
    }


    const orderId =
        orderPendingCancellation.id;


    confirmCancelButton.disabled =
        true;

    confirmCancelButton.textContent =
        "Cancelling...";


    try {

        const result = await apiRequest(
            `/orders/${orderId}`,
            {
                method: "DELETE"
            }
        );

        closeCancelOrderModal();

        showSuccessMessage(
            result?.message || `Order #${orderId} cancelled successfully.`
        );


        await loadOrders();


    } catch (error) {

        closeCancelOrderModal();


        showPageError(
            error.message ||
            "Unable to cancel order."
        );

    } finally {

        confirmCancelButton.disabled =
            false;

        confirmCancelButton.textContent =
            "Cancel Order";
    }
}


/* ============================================================
   TABLE ACTIONS
   ============================================================ */

ordersTableBody.addEventListener(
    "click",
    event => {

        const button =
            event.target.closest(
                "[data-action]"
            );


        if (!button) {
            return;
        }


        const orderId =
            Number(
                button.dataset.orderId
            );


        if (!orderId) {
            return;
        }


        const order =
            currentOrders.find(
                item =>
                    item.id === orderId
            );


        if (!order) {
            return;
        }


        const action =
            button.dataset.action;


        if (action === "view") {

            openOrderDetails(
                order
            );

        }


        if (action === "cancel") {

            if (
                normalizeStatus(
                    order.status
                ) !== "confirmed"
            ) {
                return;
            }


            openCancelOrderModal(
                order
            );
        }

    }
);


/* ============================================================
   MODAL EVENTS
   ============================================================ */

function setupModalEvents() {

    /* DETAILS */

    closeDetailsModalButton.addEventListener(
        "click",
        closeOrderDetails
    );


    closeDetailsButton.addEventListener(
        "click",
        closeOrderDetails
    );


    orderDetailsModal.addEventListener(
        "click",
        event => {

            if (
                event.target ===
                orderDetailsModal
            ) {

                closeOrderDetails();

            }

        }
    );


    /* CANCEL */

    closeCancelModalButton.addEventListener(
        "click",
        closeCancelOrderModal
    );


    cancelOrderCancelButton.addEventListener(
        "click",
        closeCancelOrderModal
    );


    confirmCancelButton.addEventListener(
        "click",
        confirmOrderCancellation
    );


    cancelOrderModal.addEventListener(
        "click",
        event => {

            if (
                event.target ===
                cancelOrderModal
            ) {

                closeCancelOrderModal();

            }

        }
    );


    /* ESCAPE */

    document.addEventListener(
        "keydown",
        event => {

            if (
                event.key !== "Escape"
            ) {
                return;
            }


            if (
                !orderDetailsModal.classList.contains(
                    "hidden"
                )
            ) {

                closeOrderDetails();

            }


            if (
                !cancelOrderModal.classList.contains(
                    "hidden"
                )
            ) {

                closeCancelOrderModal();

            }

        }
    );
}


/* ============================================================
   NAVIGATION
   ============================================================ */

function setupNavigation() {

    /*
     * Only Notifications and Events are still
     * placeholders.
     *
     * Orders, Products, Dashboard, Users and
     * Profile now use their actual page links.
     */

    const placeholderNavigationElements = [
        "notificationsNav",
    ];


    placeholderNavigationElements.forEach(
        elementId => {

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

                    window.location.href =
                        "/notifications";

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
   REFRESH
   ============================================================ */

refreshButton.addEventListener(
    "click",
    loadOrders
);


/* ============================================================
   LOADING / EMPTY STATES
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
        emptyState.querySelector("p");


    if (paragraph) {

        paragraph.textContent =
            message;
    }
}


/* ============================================================
   MESSAGES
   ============================================================ */

function hideMessages() {

    errorMessage.classList.add(
        "hidden"
    );


    successMessage.classList.add(
        "hidden"
    );
}


function showPageError(
    message
) {

    errorMessage.textContent =
        message;


    errorMessage.classList.remove(
        "hidden"
    );
}


function showSuccessMessage(
    message
) {

    successMessage.textContent =
        message;


    successMessage.classList.remove(
        "hidden"
    );


    setTimeout(
        () => {

            successMessage.classList.add(
                "hidden"
            );

        },
        3500
    );
}


/* ============================================================
   DATE FORMATTING
   ============================================================ */

function formatDate(
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


    return date.toLocaleDateString(
        undefined,
        {
            day: "2-digit",
            month: "short",
            year: "numeric"
        }
    );
}


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
        String(value ?? "");


    return div.innerHTML;
}