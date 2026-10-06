/* ============================================================
   AUTHENTICATION
   ============================================================ */

requireAuth();


/* ============================================================
   DOM ELEMENTS
   ============================================================ */

const productCountElement =
    document.getElementById("productCount");

const orderCountElement =
    document.getElementById("orderCount");

const lowStockCountElement =
    document.getElementById("lowStockCount");

const confirmedOrderCountElement =
    document.getElementById("confirmedOrderCount");

const lowStockBadge =
    document.getElementById("lowStockBadge");

const lowStockContainer =
    document.getElementById("lowStockContainer");

const recentOrdersContainer =
    document.getElementById("recentOrdersContainer");

const dashboardError =
    document.getElementById("dashboardError");

const userEmailElement =
    document.getElementById("userEmail");

const userRoleElement =
    document.getElementById("userRole");

const accountStatusElement =
    document.getElementById("accountStatus");

const apiStatusElement =
    document.getElementById("apiStatus");

const orderDescription =
    document.getElementById("orderDescription");

const adminNavigation =
    document.getElementById("adminNavigation");

const logoutButton =
    document.getElementById("logoutButton");


/* ============================================================
   CONSTANTS
   ============================================================ */

const LOW_STOCK_THRESHOLD = 5;


/* ============================================================
   PAGE INITIALIZATION
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    initializeDashboard
);


async function initializeDashboard() {

    setupNavigation();

    setupLogout();

    loadStoredUser();

    await loadDashboardData();
}


/* ============================================================
   USER INFORMATION
   ============================================================ */

function loadStoredUser() {

    const user = getStoredUser();

    if (!user) {
        return;
    }


    userEmailElement.textContent =
        user.email || "User";


    userRoleElement.textContent =
        user.role || "customer";


    const role =
        String(user.role || "").toLowerCase();


    if (role === "admin") {

        adminNavigation.classList.remove(
            "hidden"
        );

        orderDescription.textContent =
            "All orders in the system";

    } else {

        adminNavigation.classList.add(
            "hidden"
        );

        orderDescription.textContent =
            "Orders associated with your account";
    }


    const avatar =
        document.querySelector(".user-avatar");

    if (avatar && user.email) {

        avatar.textContent =
            user.email
                .charAt(0)
                .toUpperCase();
    }
}


/* ============================================================
   DASHBOARD DATA
   ============================================================ */

async function loadDashboardData() {

    try {

        const [
            products,
            orders
        ] = await Promise.all([
            getProducts(0, 100),
            getOrders()
        ]);


        apiStatusElement.textContent =
            "Connected";

        apiStatusElement.style.color =
            "var(--success)";


        updateStatistics(
            products,
            orders
        );


        renderLowStockProducts(
            products
        );


        renderRecentOrders(
            orders
        );


    } catch (error) {

        console.error(
            "Dashboard loading error:",
            error
        );


        apiStatusElement.textContent =
            "Unavailable";

        apiStatusElement.style.color =
            "var(--danger)";


        accountStatusElement.textContent =
            "Unable to load";


        dashboardError.textContent =
            error.message ||
            "Unable to load dashboard data.";


        dashboardError.classList.remove(
            "hidden"
        );


        lowStockContainer.innerHTML =
            `
            <div class="empty-state">
                Unable to load product information.
            </div>
            `;


        recentOrdersContainer.innerHTML =
            `
            <div class="empty-state">
                Unable to load order information.
            </div>
            `;
    }
}


/* ============================================================
   STATISTICS
   ============================================================ */

function updateStatistics(
    products,
    orders
) {

    productCountElement.textContent =
        products.length;


    orderCountElement.textContent =
        orders.length;


    const lowStockProducts =
        products.filter(
            product =>
                product.stock_quantity <
                LOW_STOCK_THRESHOLD
        );


    lowStockCountElement.textContent =
        lowStockProducts.length;


    lowStockBadge.textContent =
        lowStockProducts.length;


    const confirmedOrders =
        orders.filter(
            order =>
                String(order.status).toLowerCase() ===
                "confirmed"
        );


    confirmedOrderCountElement.textContent =
        confirmedOrders.length;
}


/* ============================================================
   LOW STOCK PRODUCTS
   ============================================================ */

function renderLowStockProducts(
    products
) {

    const lowStockProducts =
        products
            .filter(
                product =>
                    product.stock_quantity <
                    LOW_STOCK_THRESHOLD
            )
            .sort(
                (a, b) =>
                    a.stock_quantity -
                    b.stock_quantity
            )
            .slice(0, 5);


    if (lowStockProducts.length === 0) {

        lowStockContainer.innerHTML =
            `
            <div class="empty-state">
                No low-stock products at the moment.
            </div>
            `;

        return;
    }


    const rows =
        lowStockProducts
            .map(
                product =>
                    `
                    <tr>

                        <td class="product-name">
                            ${escapeHtml(product.name)}
                        </td>

                        <td>
                            #${product.id}
                        </td>

                        <td class="stock-warning">
                            ${product.stock_quantity}
                        </td>

                    </tr>
                    `
            )
            .join("");


    lowStockContainer.innerHTML =
        `
        <table class="dashboard-table">

            <thead>

                <tr>

                    <th>
                        Product
                    </th>

                    <th>
                        ID
                    </th>

                    <th>
                        Stock
                    </th>

                </tr>

            </thead>

            <tbody>
                ${rows}
            </tbody>

        </table>
        `;
}


/* ============================================================
   RECENT ORDERS
   ============================================================ */

function renderRecentOrders(
    orders
) {

    const recentOrders =
        [...orders]
            .sort(
                (a, b) =>
                    new Date(b.created_at) -
                    new Date(a.created_at)
            )
            .slice(0, 5);


    if (recentOrders.length === 0) {

        recentOrdersContainer.innerHTML =
            `
            <div class="empty-state">
                No orders found.
            </div>
            `;

        return;
    }


    const rows =
        recentOrders
            .map(
                order =>
                    `
                    <tr>

                        <td class="product-name">
                            #${order.id}
                        </td>

                        <td>
                            ${order.items?.length || 0}
                            item${order.items?.length === 1 ? "" : "s"}
                        </td>

                        <td>
                            ${getStatusBadge(order.status)}
                        </td>

                        <td>
                            ${formatDate(order.created_at)}
                        </td>

                    </tr>
                    `
            )
            .join("");


    recentOrdersContainer.innerHTML =
        `
        <table class="dashboard-table">

            <thead>

                <tr>

                    <th>
                        Order
                    </th>

                    <th>
                        Items
                    </th>

                    <th>
                        Status
                    </th>

                    <th>
                        Date
                    </th>

                </tr>

            </thead>

            <tbody>
                ${rows}
            </tbody>

        </table>
        `;
}


/* ============================================================
   STATUS BADGE
   ============================================================ */

function getStatusBadge(
    status
) {

    const normalizedStatus =
        String(status || "")
            .toLowerCase();


    let className =
        "status-badge";


    if (normalizedStatus === "confirmed") {

        className +=
            " status-confirmed";

    } else if (
        normalizedStatus === "cancelled"
    ) {

        className +=
            " status-cancelled";
    }


    return `
        <span class="${className}">
            ${escapeHtml(normalizedStatus)}
        </span>
    `;
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


    if (Number.isNaN(date.getTime())) {
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


/* ============================================================
   HTML ESCAPING
   ============================================================ */

function escapeHtml(
    value
) {

    const div =
        document.createElement("div");

    div.textContent =
        String(value ?? "");

    return div.innerHTML;
}


/* ============================================================
   NAVIGATION
   ============================================================ */

function setupNavigation() {

    /*
     * Products is now a real page.
     *
     * Do not prevent the normal link navigation.
     */

    const productsNav =
        document.getElementById(
            "productsNav"
        );
    
    const ordersNav=document.getElementById("ordersNav");
    const profileNav=document.getElementById("profileNav");
    const usersNav=document.getElementById("userNav");
    const eventsNav=document.getElementById("eventsNav");
    const notificationsNav=document.getElementById("notificationsNav");


    if (productsNav) {

        productsNav.addEventListener(
            "click",
            () => {

                window.location.href =
                    "/products";

            }
        );
    }
    if(ordersNav){
        ordersNav.addEventListener(
            "click",
            () => {

                window.location.href =
                    "/orders";

            }
        );
    }
    if(profileNav){
        profileNav.addEventListener(
            "click",
            () => {

                window.location.href =
                    "/profile";

            }
        );
    }
    if(usersNav){
        usersNav.addEventListener(
            "click",
            () => {

                window.location.href =
                    "/users";

            }
        );
    }

    if(eventsNav){
        eventsNav.addEventListener(
            "click",
            () => {

                window.location.href =
                    "/events";

            }
        );
    }

    if(notificationsNav){
        notificationsNav.addEventListener(
            "click",
            () => {

                window.location.href =
                    "/notifications";

            }
        );
    }


    /*
     * Other pages are still placeholders.
     */

    const placeholderNavigation = [
    ];


    placeholderNavigation.forEach(
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

                    console.log(
                        `${elementId} page will be connected in a later task.`
                    );

                }
            );
        }
    );
}


/* ============================================================
   LOGOUT
   ============================================================ */

function setupLogout() {

    if (!logoutButton) {
        return;
    }


    logoutButton.addEventListener(
        "click",
        function () {

            localStorage.removeItem(
                "access_token"
            );

            localStorage.removeItem(
                "current_user"
            );


            window.location.replace(
                "/login"
            );

        }
    );
}