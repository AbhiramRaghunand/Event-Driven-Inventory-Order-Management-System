/* ============================================================
   AUTHENTICATION
   ============================================================ */

requireAuth();


/* ============================================================
   DOM ELEMENTS
   ============================================================ */

const productsTableBody =
    document.getElementById("productsTableBody");

const loadingState =
    document.getElementById("loadingState");

const tableContainer =
    document.getElementById("tableContainer");

const emptyState =
    document.getElementById("emptyState");

const errorMessage =
    document.getElementById("errorMessage");

const successMessage =
    document.getElementById("successMessage");

const productCount =
    document.getElementById("productCount");

const refreshButton =
    document.getElementById("refreshButton");

const userEmail =
    document.getElementById("userEmail");

const userRole =
    document.getElementById("userRole");

const userInitial =
    document.getElementById("userInitial");

const adminNavigation =
    document.getElementById("adminNavigation");

const logoutButton =
    document.getElementById("logoutButton");

const addProductButton =
    document.getElementById("addProductButton");

const addProductModal =
    document.getElementById("addProductModal");

const closeModalButton =
    document.getElementById("closeModalButton");

const cancelModalButton =
    document.getElementById("cancelModalButton");

const addProductForm =
    document.getElementById("addProductForm");

const productNameInput =
    document.getElementById("productName");

const productPriceInput =
    document.getElementById("productPrice");

const productStockInput =
    document.getElementById("productStock");

const saveProductButton =
    document.getElementById("saveProductButton");

const formError =
    document.getElementById("formError");


/* EDIT */

const editProductModal =
    document.getElementById("editProductModal");

const closeEditModalButton =
    document.getElementById("closeEditModalButton");

const cancelEditModalButton =
    document.getElementById("cancelEditModalButton");

const editProductForm =
    document.getElementById("editProductForm");

const editProductId =
    document.getElementById("editProductId");

const editProductName =
    document.getElementById("editProductName");

const editProductPrice =
    document.getElementById("editProductPrice");

const editProductStock =
    document.getElementById("editProductStock");

const updateProductButton =
    document.getElementById("updateProductButton");

const editFormError =
    document.getElementById("editFormError");


/* DELETE */

const deleteProductModal =
    document.getElementById("deleteProductModal");

const closeDeleteModalButton =
    document.getElementById(
        "closeDeleteModalButton"
    );

const cancelDeleteButton =
    document.getElementById(
        "cancelDeleteButton"
    );

const confirmDeleteButton =
    document.getElementById(
        "confirmDeleteButton"
    );

const deleteProductName =
    document.getElementById(
        "deleteProductName"
    );


let productPendingDeletion = null;


/* ============================================================
   CONSTANTS
   ============================================================ */

const LOW_STOCK_THRESHOLD = 5;


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


    userInitial.textContent =
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

        addProductButton.classList.remove(
            "hidden"
        );

    } else {

        adminNavigation.classList.add(
            "hidden"
        );

        addProductButton.classList.add(
            "hidden"
        );
    }
}


/* ============================================================
   CHECK ADMIN
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
   STOCK STATUS
   ============================================================ */

function getStockStatus(stock) {

    if (stock === 0) {

        return {
            text: "Out of Stock",
            className: "status-out-of-stock"
        };

    }


    if (stock < LOW_STOCK_THRESHOLD) {

        return {
            text: "Low Stock",
            className: "status-low-stock"
        };

    }


    return {
        text: "In Stock",
        className: "status-in-stock"
    };
}


/* ============================================================
   PRICE FORMATTING
   ============================================================ */

function formatPrice(price) {

    return new Intl.NumberFormat(
        "en-IN",
        {
            style: "currency",
            currency: "INR"
        }
    ).format(price);
}


/* ============================================================
   RENDER PRODUCTS
   ============================================================ */

function renderProducts(products) {

    productsTableBody.innerHTML = "";

    productCount.textContent =
        products.length;


    if (products.length === 0) {

        tableContainer.classList.add(
            "hidden"
        );

        emptyState.classList.remove(
            "hidden"
        );

        return;
    }


    emptyState.classList.add(
        "hidden"
    );

    tableContainer.classList.remove(
        "hidden"
    );


    const admin =
        isAdmin();


    products.forEach(
        product => {

            const row =
                document.createElement("tr");


            const stockStatus =
                getStockStatus(
                    product.stock_quantity
                );


            const actionButtons =
                admin
                    ? `
                        <td class="actions-cell">

                            <button
                                type="button"
                                class="action-button"
                                data-action="edit"
                                data-product-id="${product.id}"
                            >
                                Edit
                            </button>

                            <button
                                type="button"
                                class="action-button delete-button"
                                data-action="delete"
                                data-product-id="${product.id}"
                            >
                                Delete
                            </button>

                        </td>
                    `
                    : `
                        <td class="actions-cell">
                            —
                        </td>
                    `;


            row.innerHTML =
                `
                <td>
                    <span class="product-id">
                        #${product.id}
                    </span>
                </td>

                <td>
                    <span class="product-name">
                        ${escapeHtml(product.name)}
                    </span>
                </td>

                <td>
                    <span class="price">
                        ${formatPrice(product.price)}
                    </span>
                </td>

                <td>
                    <span class="stock-number">
                        ${product.stock_quantity}
                    </span>
                </td>

                <td>
                    <span
                        class="status-badge ${stockStatus.className}"
                    >
                        ${stockStatus.text}
                    </span>
                </td>

                ${actionButtons}
                `;


            productsTableBody.appendChild(
                row
            );

        }
    );
}


/* ============================================================
   HTML ESCAPING
   ============================================================ */

function escapeHtml(value) {

    const div =
        document.createElement("div");


    div.textContent =
        String(value ?? "");


    return div.innerHTML;
}


/* ============================================================
   LOAD PRODUCTS
   ============================================================ */

async function loadProducts() {

    loadingState.classList.remove(
        "hidden"
    );

    tableContainer.classList.add(
        "hidden"
    );

    emptyState.classList.add(
        "hidden"
    );

    errorMessage.classList.add(
        "hidden"
    );


    try {

        const products =
            await getProducts();


        renderProducts(
            products
        );

    } catch (error) {

        errorMessage.textContent =
            error.message ||
            "Unable to load products.";

        errorMessage.classList.remove(
            "hidden"
        );

    } finally {

        loadingState.classList.add(
            "hidden"
        );
    }
}


/* ============================================================
   ADD PRODUCT MODAL
   ============================================================ */

function openAddProductModal() {

    formError.textContent = "";

    formError.classList.add(
        "hidden"
    );


    addProductForm.reset();


    addProductModal.classList.remove(
        "hidden"
    );


    productNameInput.focus();
}


function closeAddProductModal() {

    addProductModal.classList.add(
        "hidden"
    );


    formError.textContent = "";

    formError.classList.add(
        "hidden"
    );


    addProductForm.reset();
}


/* ============================================================
   ADD PRODUCT
   ============================================================ */

async function handleAddProduct(event) {

    event.preventDefault();


    formError.textContent = "";

    formError.classList.add(
        "hidden"
    );


    const name =
        productNameInput.value.trim();


    const price =
        Number(
            productPriceInput.value
        );


    const stockQuantity =
        Number(
            productStockInput.value
        );


    if (!name) {

        showFormError(
            "Product name is required."
        );

        productNameInput.focus();

        return;
    }


    if (
        !Number.isFinite(price) ||
        price <= 0
    ) {

        showFormError(
            "Price must be greater than 0."
        );

        productPriceInput.focus();

        return;
    }


    if (
        !Number.isInteger(stockQuantity) ||
        stockQuantity < 0
    ) {

        showFormError(
            "Stock quantity must be a whole number greater than or equal to 0."
        );

        productStockInput.focus();

        return;
    }


    saveProductButton.disabled =
        true;

    saveProductButton.textContent =
        "Adding...";


    try {

        await createProduct(
            name,
            price,
            stockQuantity
        );


        closeAddProductModal();


        showSuccessMessage(
            "Product added successfully."
        );


        await loadProducts();


    } catch (error) {

        showFormError(
            error.message ||
            "Unable to add product."
        );

    } finally {

        saveProductButton.disabled =
            false;

        saveProductButton.textContent =
            "Add Product";
    }
}


/* ============================================================
   EDIT PRODUCT
   ============================================================ */

function openEditProductModal(product) {

    editProductId.value =
        product.id;


    editProductName.value =
        product.name;


    editProductPrice.value =
        product.price;


    editProductStock.value =
        product.stock_quantity;


    editFormError.textContent = "";

    editFormError.classList.add(
        "hidden"
    );


    editProductModal.classList.remove(
        "hidden"
    );


    editProductName.focus();
}


function closeEditProductModal() {

    editProductModal.classList.add(
        "hidden"
    );


    editFormError.textContent = "";

    editFormError.classList.add(
        "hidden"
    );


    editProductForm.reset();
}


async function handleEditProduct(event) {

    event.preventDefault();


    editFormError.textContent = "";

    editFormError.classList.add(
        "hidden"
    );


    const productId =
        Number(
            editProductId.value
        );


    const name =
        editProductName.value.trim();


    const price =
        Number(
            editProductPrice.value
        );


    const stockQuantity =
        Number(
            editProductStock.value
        );


    if (!name) {

        showEditFormError(
            "Product name is required."
        );

        editProductName.focus();

        return;
    }


    if (
        !Number.isFinite(price) ||
        price <= 0
    ) {

        showEditFormError(
            "Price must be greater than 0."
        );

        editProductPrice.focus();

        return;
    }


    if (
        !Number.isInteger(stockQuantity) ||
        stockQuantity < 0
    ) {

        showEditFormError(
            "Stock quantity must be a whole number greater than or equal to 0."
        );

        editProductStock.focus();

        return;
    }


    updateProductButton.disabled =
        true;

    updateProductButton.textContent =
        "Saving...";


    try {

        await updateProduct(
            productId,
            name,
            price,
            stockQuantity
        );


        closeEditProductModal();


        showSuccessMessage(
            "Product updated successfully."
        );


        await loadProducts();


    } catch (error) {

        showEditFormError(
            error.message ||
            "Unable to update product."
        );

    } finally {

        updateProductButton.disabled =
            false;

        updateProductButton.textContent =
            "Save Changes";
    }
}


/* ============================================================
   DELETE MODAL
   ============================================================ */

function openDeleteProductModal(product) {

    productPendingDeletion =
        product;


    deleteProductName.textContent =
        product.name;


    deleteProductModal.classList.remove(
        "hidden"
    );
}


function closeDeleteProductModal() {

    deleteProductModal.classList.add(
        "hidden"
    );


    productPendingDeletion =
        null;
}


/* ============================================================
   DELETE PRODUCT
   ============================================================ */

async function confirmDeleteProduct() {

    if (!productPendingDeletion) {
        return;
    }


    const productId =
        productPendingDeletion.id;


    confirmDeleteButton.disabled =
        true;

    confirmDeleteButton.textContent =
        "Deleting...";


    try {

        await deleteProduct(
            productId
        );


        closeDeleteProductModal();


        showSuccessMessage(
            "Product deleted successfully."
        );


        await loadProducts();


    } catch (error) {

        closeDeleteProductModal();


        showPageError(
            error.message ||
            "Unable to delete product."
        );

    } finally {

        confirmDeleteButton.disabled =
            false;

        confirmDeleteButton.textContent =
            "Delete Product";
    }
}


/* ============================================================
   TABLE ACTIONS
   ============================================================ */

productsTableBody.addEventListener(
    "click",
    async event => {

        const button =
            event.target.closest(
                "[data-action]"
            );


        if (!button) {
            return;
        }


        const productId =
            Number(
                button.dataset.productId
            );


        if (
            !productId ||
            !isAdmin()
        ) {
            return;
        }


        const action =
            button.dataset.action;


        if (action === "edit") {

            try {

                const product =
                    await getProduct(
                        productId
                    );


                openEditProductModal(
                    product
                );

            } catch (error) {

                showPageError(
                    error.message ||
                    "Unable to load product."
                );
            }

        }


        if (action === "delete") {

            try {

                const product =
                    await getProduct(
                        productId
                    );


                openDeleteProductModal(
                    product
                );

            } catch (error) {

                showPageError(
                    error.message ||
                    "Unable to load product."
                );
            }

        }

    }
);


/* ============================================================
   ERRORS
   ============================================================ */

function showFormError(message) {

    formError.textContent =
        message;

    formError.classList.remove(
        "hidden"
    );
}


function showEditFormError(message) {

    editFormError.textContent =
        message;

    editFormError.classList.remove(
        "hidden"
    );
}


function showPageError(message) {

    errorMessage.textContent =
        message;

    errorMessage.classList.remove(
        "hidden"
    );
}


/* ============================================================
   SUCCESS MESSAGE
   ============================================================ */

function showSuccessMessage(message) {

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
   LOGOUT
   ============================================================ */

logoutButton.addEventListener(
    "click",
    () => {

        logout();

    }
);


/* ============================================================
   NAVIGATION
   ============================================================ */

function setupNavigation() {

    const notificationsNav =
        document.getElementById(
            "notificationsNav"
        );

    const eventsNav =
        document.getElementById(
            "eventsNav"
        );


    if (notificationsNav) {

        notificationsNav.addEventListener(
            "click",
            event => {

                window.location.href =
                    "/frontend/pages/notifications/notifications.html";


            }
        );

    }


    if (eventsNav) {

        eventsNav.addEventListener(
            "click",
            event => {

                // event.preventDefault();

                window.location.href =
                    "/frontend/pages/events/events.html";

            }
        );

    }
}


setupNavigation();


/* ============================================================
   MODAL EVENTS
   ============================================================ */

/* ADD */

addProductButton.addEventListener(
    "click",
    openAddProductModal
);


closeModalButton.addEventListener(
    "click",
    closeAddProductModal
);


cancelModalButton.addEventListener(
    "click",
    closeAddProductModal
);


addProductForm.addEventListener(
    "submit",
    handleAddProduct
);


/* EDIT */

editProductForm.addEventListener(
    "submit",
    handleEditProduct
);


closeEditModalButton.addEventListener(
    "click",
    closeEditProductModal
);


cancelEditModalButton.addEventListener(
    "click",
    closeEditProductModal
);


/* DELETE */

closeDeleteModalButton.addEventListener(
    "click",
    closeDeleteProductModal
);


cancelDeleteButton.addEventListener(
    "click",
    closeDeleteProductModal
);


confirmDeleteButton.addEventListener(
    "click",
    confirmDeleteProduct
);


/* ============================================================
   MODAL BACKGROUND
   ============================================================ */

addProductModal.addEventListener(
    "click",
    event => {

        if (
            event.target ===
            addProductModal
        ) {

            closeAddProductModal();

        }

    }
);


editProductModal.addEventListener(
    "click",
    event => {

        if (
            event.target ===
            editProductModal
        ) {

            closeEditProductModal();

        }

    }
);


deleteProductModal.addEventListener(
    "click",
    event => {

        if (
            event.target ===
            deleteProductModal
        ) {

            closeDeleteProductModal();

        }

    }
);


/* ============================================================
   ESCAPE KEY
   ============================================================ */

document.addEventListener(
    "keydown",
    event => {

        if (event.key !== "Escape") {
            return;
        }


        if (
            !addProductModal.classList.contains(
                "hidden"
            )
        ) {

            closeAddProductModal();

        }


        if (
            !editProductModal.classList.contains(
                "hidden"
            )
        ) {

            closeEditProductModal();

        }


        if (
            !deleteProductModal.classList.contains(
                "hidden"
            )
        ) {

            closeDeleteProductModal();

        }

    }
);


/* ============================================================
   REFRESH
   ============================================================ */

refreshButton.addEventListener(
    "click",
    loadProducts
);


/* ============================================================
   INITIALIZATION
   ============================================================ */

loadUserInformation();

loadProducts();