from .base_settings import *  # noqa

DEBUG = True

CORS_ORIGIN_ALLOW_ALL = DEBUG


# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
DEFAULT_FROM_EMAIL = ""
EMAIL_HOST = ""
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
EMAIL_USE_TLS = True
EMAIL_PORT = 25
