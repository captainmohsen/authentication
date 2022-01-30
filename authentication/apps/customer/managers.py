from django.contrib.auth.models import BaseUserManager
from django.db.models import Manager


class ContactCustomerManager(BaseUserManager):
    def create_customer(self, contact, password=None, **kwargs):
        customer = self.model(username=contact, **kwargs)

        customer.set_password(password)
        customer.save(using=self._db)
        return customer


class ExcludeDeletedEntityManager(Manager):
    def get_queryset(self):
        return (
            super(ExcludeDeletedEntityManager, self)
            .get_queryset()
            .filter(deleted_at=None)
        )
