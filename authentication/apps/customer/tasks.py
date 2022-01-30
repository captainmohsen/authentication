from celery import shared_task
from django.conf import settings

from authentication.apps.customer.models import Contact, EmailChange, EmailTemp, OTPTemp
from authentication.utils import send_email


@shared_task(name="customer.send_email_verification")
def send_email_verification(contact_id):

    contact = Contact.objects.get(id=contact_id)
    temp = EmailTemp.objects.create(customer=contact.customer, email=contact.email)
    email_change = EmailChange.objects.filter(customer=contact.customer).latest(
        "created_at"
    )

    url = settings.URL_TEMPLATES["EMAIL_VERIFICATION_URL_TEMPLATE"].format(
        customer_id=temp.customer.id, temp_id=temp.id
    )
    context = {"verification_url": url}
    if contact.customer.email_verify is None and email_change.new_email:
        send_email("customer", "email_verification", context, [email_change.new_email])
    else:
        send_email("customer", "email_verification", context, [contact.email])


@shared_task(name="customer.send_mobile_verification_code")
def send_mobile_verification_code(contact_id):
    # code = random.randint(1000, 9999)  # noqa S311
    code = 1234

    # Send To Phone Here

    contact = Contact.objects.get(id=contact_id)
    OTPTemp.objects.create(customer=contact.customer, code=code)
