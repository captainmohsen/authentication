import os

DOMAIN = os.environ.get("DOMAIN", "http://172.16.7.218:9000")

URL_TEMPLATES = {
    "EMAIL_VERIFICATION_URL_TEMPLATE": DOMAIN
    + "/sign-up/verify-email/{customer_id}/{temp_id}",
}
