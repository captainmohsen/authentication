from .base_settings import *  # noqa

DEBUG = True

CORS_ORIGIN_ALLOW_ALL = DEBUG


# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@khallagh.com"
EMAIL_HOST = "mail.khallagh.com"
EMAIL_HOST_USER = "noreply@khallagh.com"
EMAIL_HOST_PASSWORD = "Khallagh@dashboard@123"
EMAIL_USE_TLS = True
EMAIL_PORT = 25
