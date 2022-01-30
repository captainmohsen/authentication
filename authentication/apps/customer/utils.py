import requests
from django.conf import settings


def validate_recaptcha(response):
    data = {
        "secret": settings.AUTHENTICATION_CUSTOMER["RECAPTCHA"]["KEY"]["SECRET"],
        "response": response,
    }
    try:
        validation_response = requests.post(
            settings.AUTHENTICATION_CUSTOMER["RECAPTCHA"]["URL"], data
        ).json()
        if validation_response.get("success", False):
            return True
        return False
    except requests.exceptions.RequestException:
        return False
