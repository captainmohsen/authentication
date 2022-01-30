from datetime import timedelta

# Customer APP
AUTHENTICATION_CUSTOMER = {
    "RECAPTCHA": {
        "ENABLED": False,
        "KEY": {
            "SECRET": "6LeyQGQdAAAAAC3UX7TM_o3EI4Sfwtd5zYhd3xRy",
        },
        "URL": "https://www.google.com/recaptcha/api/siteverify",
    },
    "EMAIL_VERIFICATION_EXPIRE_TIME": timedelta(seconds=100),
    "EMAIL_VERIFICATION_CHANGE_LIMIT": 3,
    "EMAIL_VERIFICATION_RESEND_TIME_LIMIT": timedelta(seconds=100),
    "OTP_EXPIRE_TIME": timedelta(seconds=100),
}

PUBLIC_APP_SETTING = []
