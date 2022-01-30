from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ObjectDoesNotExist

from authentication.apps.customer import models


class EmailMobileAuthentication(ModelBackend):
    def authenticate(
        self, request, username=None, mobile=None, email=None, password=None, **kwargs
    ):
        if email:
            try:
                contact = models.Contact.objects.get(email=email)
                customer = contact.customer

            except ObjectDoesNotExist:
                return None
            else:
                if customer.check_password(password) and self.user_can_authenticate(
                    customer.username
                ):
                    return customer

        elif mobile:

            try:  # to allow authentication through mobile
                contact = models.Contact.objects.get(mobile=mobile)
                customer = contact.customer

            except ObjectDoesNotExist:
                return None
            else:
                if customer.check_password(password) and self.user_can_authenticate(
                    customer.username
                ):
                    return customer

    def get_user(self, contact_id):
        try:
            customer = models.Customer.objects.get(pk=contact_id)
        except ObjectDoesNotExist:
            return None

        return customer if self.user_can_authenticate(customer.username) else None
