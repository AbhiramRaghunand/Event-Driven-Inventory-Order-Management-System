const registerForm =
    document.getElementById("registerForm");

const registerButton =
    document.getElementById("registerButton");

const registerMessage =
    document.getElementById("registerMessage");


registerForm.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();

        registerMessage.textContent = "";
        registerMessage.className = "message";


        const email =
            document
                .getElementById("email")
                .value
                .trim();

        const password =
            document
                .getElementById("password")
                .value;

        const confirmPassword =
            document
                .getElementById("confirmPassword")
                .value;


        /*
         * Validate password confirmation
         * before sending the request.
         */

        if (password !== confirmPassword) {

            registerMessage.textContent =
                "Passwords do not match.";

            registerMessage.className =
                "error-message";

            return;
        }


        registerButton.disabled = true;

        registerButton.textContent =
            "Creating account...";


        try {

            await registerUser(
                email,
                password,
                confirmPassword
            );


            registerMessage.textContent =
                "Account created successfully. Redirecting to login...";

            registerMessage.className =
                "success-message";


            setTimeout(() => {

                window.location.href =
                    "/login";

            }, 1200);


        } catch (error) {

            /*
             * Pydantic/FastAPI validation errors
             * can sometimes contain a structured
             * array instead of a simple detail string.
             */

            if (Array.isArray(error.message)) {

                registerMessage.textContent =
                    "Please check your registration details.";

            } else {

                registerMessage.textContent =
                    error.message;
            }

            registerMessage.className =
                "error-message";

        } finally {

            registerButton.disabled = false;

            registerButton.textContent =
                "Create Account";
        }

    }
);