# Parametrized test cases for user registration form validation
(
    PARAM_INVALID_EMAIL,
    PARAM_PASSWORD_NOT_MATCH,
    PARAM_PASSWORD_TOO_SHORT,
    PARAM_EMPTY_SPACES,
    PARAM_INVALID_PASSWORD_V1,
    PARAM_INVALID_PASSWORD_V2,
) = [
    (
        "Invalid Email",
        {
            "email": "invalid-email",
            "password": "Test1234!",
            "password_confirm": "Test1234!",
        },
        "Enter a valid email address.",
    ),
    (
        "Passwords do not match",
        {
            "email": "test@example.com",
            "password": "Test1234!",
            "password_confirm": "DifferentPass123!",
        },
        "Passwords do not match",
    ),
    (
        "Password too short",
        {
            "email": "test@example.com",
            "password": "Test",
            "password_confirm": "Test",
        },
        "Ensure this value has at least 8 characters",
    ),
    (
        "Empty Spaces",
        {
            "email": "",
            "password": "",
            "password_confirm": "",
        },
        "This field is required",
    ),
    (
        "Invalid Password",
        {
            "email": "test@example.com",
            "password": "12345678",
            "password_confirm": "12345678",
        },
        [
            "Invalid password.",
            "Password must contain:",
            "At least one uppercase letter.",
            "At least one lowercase letter.",
            "At least one symbol",
        ],
    ),
    (
        "Invalid Password 2",
        {
            "email": "test@example.com",
            "password": "weakpassword",
            "password_confirm": "weakpassword",
        },
        [
            "Password must contain:",
            "At least one uppercase letter.",
            "At least one number.",
            "At least one symbol",
        ],
    ),
]
