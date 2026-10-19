
requireAuth();

const CART_STORAGE_KEY = "inventory_cart";
const PENDING_ORDER_KEY = "inventory_pending_order_id";

const userEmail = document.getElementById("userEmail");
const userRole = document.getElementById("userRole");
const userInitial = document.getElementById("userInitial");
const adminNavigation = document.getElementById("adminNavigation");
const logoutButton = document.getElementById("logoutButton");
const cartItemsElement = document.getElementById("cartItems");
const loadingState = document.getElementById("loadingState");
const emptyState = document.getElementById("emptyState");
const cartSummary = document.getElementById("cartSummary");
const cartPageCount = document.getElementById("cartPageCount");
const cartDescription = document.getElementById("cartDescription");
const totalItems = document.getElementById("totalItems");
const totalPrice = document.getElementById("totalPrice");
const placeOrderButton = document.getElementById("placeOrderButton");
const errorMessage = document.getElementById("errorMessage");
const successMessage = document.getElementById("successMessage");

let cartItems = [];
let currentProducts = [];

function getPendingOrderId() {
    const value = localStorage.getItem(PENDING_ORDER_KEY);

    if (!value || !/^\d+$/.test(value)) {
        return null;
    }

    return Number(value);
}

function savePendingOrderId(orderId) {
    localStorage.setItem(PENDING_ORDER_KEY, String(orderId));
}

function clearPendingOrderId() {
    localStorage.removeItem(PENDING_ORDER_KEY);
}

function formatPrice(price) {
    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR"
    }).format(price);
}

function escapeHtml(value) {
    const element = document.createElement("div");
    element.textContent = String(value ?? "");
    return element.innerHTML;
}

function saveCart() {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cartItems));
}

function loadCart() {
    try {
        const savedCart = JSON.parse(
            localStorage.getItem(CART_STORAGE_KEY) || "[]"
        );

        cartItems = Array.isArray(savedCart)
            ? savedCart.filter(item => (
                item &&
                Number.isInteger(Number(item.product_id)) &&
                Number.isInteger(Number(item.quantity)) &&
                Number(item.quantity) > 0
            )).map(item => ({
                product_id: Number(item.product_id),
                name: String(item.name || "Product"),
                price: Number(item.price) || 0,
                available_stock: Number(item.available_stock) || 0,
                quantity: Number(item.quantity)
            }))
            : [];
    } catch (error) {
        cartItems = [];
        saveCart();
    }
}

function showError(message) {
    successMessage.classList.add("hidden");
    errorMessage.textContent = message;
    errorMessage.classList.remove("hidden");
}

function showSuccess(message) {
    errorMessage.classList.add("hidden");
    successMessage.textContent = message;
    successMessage.classList.remove("hidden");
}

function reconcileCart() {
    const productsById = new Map(
        currentProducts.map(product => [String(product.id), product])
    );

    cartItems = cartItems.map(item => {
        const product = productsById.get(String(item.product_id));

        if (!product || product.stock_quantity <= 0) {
            return null;
        }

        return {
            product_id: product.id,
            name: product.name,
            price: Number(product.price),
            available_stock: product.stock_quantity,
            quantity: Math.min(item.quantity, product.stock_quantity)
        };
    }).filter(item => item && item.quantity > 0);

    saveCart();
}

function getItemCount() {
    return cartItems.reduce(
        (count, item) => count + item.quantity,
        0
    );
}

function renderCart() {
    cartItemsElement.innerHTML = "";

    const itemCount = getItemCount();
    const cartHasItems = cartItems.length > 0;

    cartPageCount.textContent =
        `${itemCount} ${itemCount === 1 ? "item" : "items"}`;

    cartDescription.textContent = cartHasItems
        ? "Review quantities before placing your order."
        : "Your selected products";

    totalItems.textContent = itemCount;

    if (!cartHasItems) {
        cartItemsElement.classList.add("hidden");
        emptyState.classList.remove("hidden");
        cartSummary.classList.add("hidden");
        return;
    }

    cartItemsElement.classList.remove("hidden");
    emptyState.classList.add("hidden");
    cartSummary.classList.remove("hidden");

    let total = 0;

    cartItems.forEach(item => {
        total += item.price * item.quantity;

        const element = document.createElement("div");
        element.className = "cart-item";

        element.innerHTML = `
            <div class="cart-item-details">
                <strong class="cart-item-name">
                    ${escapeHtml(item.name)}
                </strong>
                <span class="cart-item-meta">
                    ${formatPrice(item.price)} each ·
                    ${item.available_stock} available
                </span>
            </div>

            <div class="cart-item-controls">
                <div class="quantity-controls">
                    <button
                        type="button"
                        class="quantity-button"
                        data-action="decrease"
                        data-product-id="${item.product_id}"
                        aria-label="Decrease quantity"
                    >−</button>

                    <span class="cart-item-quantity">
                        ${item.quantity}
                    </span>

                    <button
                        type="button"
                        class="quantity-button"
                        data-action="increase"
                        data-product-id="${item.product_id}"
                        aria-label="Increase quantity"
                        ${item.quantity >= item.available_stock ? "disabled" : ""}
                    >+</button>
                </div>

                <strong class="cart-item-total">
                    ${formatPrice(item.price * item.quantity)}
                </strong>

                <button
                    type="button"
                    class="cart-remove-button"
                    data-action="remove"
                    data-product-id="${item.product_id}"
                >Remove</button>
            </div>
        `;

        cartItemsElement.appendChild(element);
    });

    totalPrice.textContent = formatPrice(total);
}

function updateQuantity(productId, change) {
    const item = cartItems.find(
        cartItem => String(cartItem.product_id) === String(productId)
    );

    if (!item) {
        return;
    }

    if (item.quantity + change < 1) {
        removeItem(productId);
        return;
    }

    item.quantity = Math.min(
        Math.max(1, item.quantity + change),
        item.available_stock
    );

    saveCart();
    renderCart();
}

function removeItem(productId) {
    cartItems = cartItems.filter(
        item => String(item.product_id) !== String(productId)
    );

    saveCart();
    renderCart();
}

async function placeOrder() {
    if (cartItems.length === 0) {
        return;
    }

    if (typeof Razorpay === "undefined") {
        showError(
            "Payment gateway could not load. Please refresh and try again."
        );
        return;
    }

    placeOrderButton.disabled = true;
    placeOrderButton.textContent = "Creating Order...";
    errorMessage.classList.add("hidden");
    successMessage.classList.add("hidden");

    try {
        // Reuse a saved order ID when retrying payment.
        let order;
        const pendingOrderId = getPendingOrderId();

        if (pendingOrderId) {
            order = { id: pendingOrderId };
        } else {
            order = await createOrder(
                cartItems.map(item => ({
                    product_id: item.product_id,
                    quantity: item.quantity
                }))
            );

            savePendingOrderId(order.id);
        }

        // Create or reuse a Razorpay payment order for this inventory order.
        const paymentOrder = await createPaymentOrder(order.id);

        const options = {
            key: paymentOrder.razorpay_key_id,
            amount: Math.round(Number(paymentOrder.amount) * 100),
            currency: paymentOrder.currency || "INR",
            name: "Inventory Management System",
            description: `Payment for Order #${order.id}`,
            order_id: paymentOrder.razorpay_order_id,

            handler: async function (response) {
                placeOrderButton.disabled = true;
                placeOrderButton.textContent = "Verifying Payment...";

                try {
                    const result = await verifyPayment(response);

                    // Clear the cart only after backend verification succeeds.
                    cartItems = [];
                    saveCart();
                    clearPendingOrderId();
                    renderCart();

                    showSuccess(
                        `Payment successful! Order #${result.order_id} is verified.`
                    );
                } catch (error) {
                    showError(
                        "Payment may have succeeded, but verification failed. " +
                        "Please contact support before attempting another payment. " +
                        `${error.message || ""}`
                    );
                } finally {
                    placeOrderButton.disabled = false;
                    placeOrderButton.textContent = "Place Order";
                }
            },

            modal: {
                ondismiss: async function () {
                    try {
                        const result = await apiRequest(
                            `/payments/orders/${order.id}/cancel`,
                            { method: "POST" }
                        );

                        // Clear the saved ID only after confirmed cancellation.
                        clearPendingOrderId();

                        showSuccess(
                            result.message ||
                            "Order cancelled and stock restored."
                        );
                    } catch (error) {
                        console.error(
                            "Order cancellation failed:",
                            error
                        );

                        showError(
                            "Checkout was closed, but cancellation could not " +
                            "be confirmed. Please check your order status."
                        );
                    } finally {
                        placeOrderButton.disabled = false;
                        placeOrderButton.textContent = "Place Order";
                    }
                }
            },

            theme: {
                color: "#2563eb"
            }
        };

        const checkout = new Razorpay(options);

        // Keep only one payment.failed handler.
        checkout.on("payment.failed", function (response) {
            placeOrderButton.disabled = false;
            placeOrderButton.textContent = "Place Order";

            showError(
                response.error?.description ||
                "Payment failed. Your order may still exist; " +
                "check its status before retrying."
            );
        });

        checkout.open();

    } catch (error) {
        showError(
            error.message ||
            "Unable to initiate checkout. Check your order and payment status."
        );

        placeOrderButton.disabled = false;
        placeOrderButton.textContent = "Place Order";
    }
}

function loadUserInformation() {
    const user = getStoredUser();

    if (!user) {
        return;
    }

    userEmail.textContent = user.email || "User";
    userRole.textContent = user.role || "customer";
    userInitial.textContent =
        (user.email || "U").charAt(0).toUpperCase();

    if (String(user.role || "").toLowerCase() === "admin") {
        adminNavigation.classList.remove("hidden");
        placeOrderButton.classList.add("hidden");
        cartDescription.textContent =
            "Cart ordering is available for customers.";
    }
}

cartItemsElement.addEventListener("click", event => {
    const button = event.target.closest("[data-action]");

    if (!button) {
        return;
    }

    const productId = button.dataset.productId;
    const action = button.dataset.action;

    if (action === "increase") {
        updateQuantity(productId, 1);
    }

    if (action === "decrease") {
        updateQuantity(productId, -1);
    }

    if (action === "remove") {
        removeItem(productId);
    }
});

placeOrderButton.addEventListener("click", placeOrder);
logoutButton.addEventListener("click", logout);

async function initialize() {
    loadUserInformation();
    loadCart();

    try {
        currentProducts = await getProducts();
        reconcileCart();
        renderCart();
    } catch (error) {
        loadingState.classList.add("hidden");
        showError(error.message || "Unable to refresh cart stock.");
        renderCart();
    } finally {
        loadingState.classList.add("hidden");
    }
}

initialize();
