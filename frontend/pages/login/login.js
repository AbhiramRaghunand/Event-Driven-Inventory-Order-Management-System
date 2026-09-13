const loginForm =
    document.getElementById("loginForm");

const loginButton =
    document.getElementById("loginButton");

const loginMessage =
    document.getElementById("loginMessage");


loginForm.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();

        loginMessage.textContent = "";
        loginMessage.className = "message";


        const email =
            document
                .getElementById("email")
                .value
                .trim();

        const password =
            document
                .getElementById("password")
                .value;


        loginButton.disabled = true;
        loginButton.textContent =
            "Signing in...";


        try {

            /*
             * Authenticate the user.
             */

            const data =
                await loginUser(
                    email,
                    password
                );


            /*
             * Retrieve the authenticated user.
             *
             * This gives us the user's
             * role for RBAC and the dashboard.
             */

            saveAuth(
                data.access_token
            );


            const user =
                await getCurrentUser();


            /*
             * Store both the JWT and
             * authenticated user information.
             */

            saveAuth(
                data.access_token,
                user
            );


            /*
             * Authentication successful.
             *
             * Go directly to the dashboard
             * instead of going through /frontend/.
             */

            window.location.href =
                "/frontend/pages/dashboard/dashboard.html";


        } catch (error) {

            loginMessage.textContent =
                error.message;

            loginMessage.className =
                "error-message";

        } finally {

            loginButton.disabled = false;

            loginButton.textContent =
                "Sign In";
        }

    }
);