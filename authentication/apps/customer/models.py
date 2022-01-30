from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core import validators
from django.db import models
from django.utils.translation import gettext_lazy as _

from authentication.apps.customer.fields import (
    NullableUniqueCharField,
    NullableUniqueEmailField,
)
from authentication.apps.customer.managers import ContactCustomerManager
from authentication.apps.customer.validators import validate_national_code
from authentication.models import EntityMixin


class Contact(EntityMixin):
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.UUIDField(blank=True, null=True)  # noqa DJ01
    owner = GenericForeignKey("content_type", "object_id")

    email = NullableUniqueEmailField(
        _("email address"),
        max_length=75,
        blank=True,
        default=None,
        unique=True,
        null=True,
        error_messages={
            "unique": _("This email already used"),
            "max_length": _("Enter a valid email address"),
            "invalid": _("Enter a valid email address"),
        },
    )

    mobile = NullableUniqueCharField(
        _("mobile"),
        max_length=15,
        unique=True,
        default=None,
        blank=True,
        null=True,
        validators=[
            validators.RegexValidator(
                r"^(?:0|98|\+98|\+980|0098|098|00980)?(9\d{9})$",
                _("Enter a valid mobile"),
                "invalid",
            )
        ],
        error_messages={
            "unique": _("This mobile already used"),
            "max_length": _("Enter a valid mobile"),
            "invalid": _("Enter a valid mobile"),
        },
    )

    telephone = models.CharField(
        _("telephone"),
        max_length=15,
        default="",
        blank=True,
        validators=[validators.int_list_validator(sep="")],
        error_messages={
            "max_length": _("Enter a valid telephone"),
            "invalid": _("Enter a valid telephone"),
        },
    )

    city = models.CharField(max_length=50, default="", blank=True)

    province = models.CharField(max_length=50, default="", blank=True)

    postal_code = models.CharField(
        _("postal code"),
        max_length=10,
        default="",
        blank=True,
        validators=[validators.int_list_validator(sep="")],
        error_messages={
            "max_length": _("Enter a valid postal code"),
            "invalid": _("Enter a valid postal code"),
        },
    )

    address = models.CharField(max_length=254, default="", blank=True)


class Customer(AbstractBaseUser, EntityMixin):
    username = models.OneToOneField(
        Contact, on_delete=models.RESTRICT, related_name="customer"
    )

    password = models.CharField(
        max_length=128,
        validators=[
            validators.RegexValidator(
                regex=r"\d",
                message=_("Ensure Password has at least one digit"),
            ),
            validators.RegexValidator(
                regex="[a-zA-Z]",
                message=_("Ensure Password has at least one latin letter"),
            ),
            validators.MinLengthValidator(8),
        ],
        error_messages={"required": _("Password required")},
    )

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.UUIDField(blank=True, null=True)  # noqa DJ01
    owner = GenericForeignKey("content_type", "object_id")

    is_active = models.BooleanField(
        _("active"),
        default=False,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )

    email_verify = models.DateTimeField(null=True, blank=True)

    mobile_verify = models.DateTimeField(null=True, blank=True)

    total_credit = models.BigIntegerField(default=0)

    USERNAME_FIELD = "username"

    objects = ContactCustomerManager()

    # def delete(self, using=None, keep_parents=False):
    #     super(Customer, self).delete(using=using, keep_parents=keep_parents)
    #     self.username.delete()
    #     self.people.delete()


class People(EntityMixin):
    class SEXES:
        MALE = "M"
        FEMALE = "F"
        UNSURE = "U"

        SEX_CHOICES = (
            (
                FEMALE,
                _("Female"),
            ),
            (
                MALE,
                _("Male"),
            ),
            (
                UNSURE,
                _("Unsure"),
            ),
        )

    contact = GenericRelation(Contact, related_query_name="people")

    customer = GenericRelation(Customer, related_query_name="people")

    name = models.CharField(max_length=50, default="", blank=True)

    last_name = models.CharField(max_length=50, default="", blank=True)

    id_number = models.CharField(max_length=15, default="", blank=True)

    national_code = models.CharField(
        _("national code"),
        unique=True,
        max_length=10,
        validators=[
            validate_national_code,
        ],
        error_messages={
            "unique": _("This national code already used"),
            "invalid": _("Enter a valid national code"),
        },
    )

    birth_date = models.DateField(default=None, null=True, blank=True)

    sex = models.CharField(
        max_length=1, choices=SEXES.SEX_CHOICES, default=SEXES.UNSURE
    )


class Company(EntityMixin):
    agent = models.OneToOneField(
        People, on_delete=models.SET_NULL, null=True, related_name="company"
    )

    contact = GenericRelation(Contact, related_query_name="company")

    customer = GenericRelation(Customer, related_query_name="company")

    name = models.CharField(max_length=50, null=False)

    national_code = models.CharField(
        _("national code"),
        unique=True,
        max_length=10,
        validators=[
            validate_national_code,
        ],
        error_messages={
            "unique": _("This national code already used"),
            "invalid": _("Enter a valid national code"),
        },
    )

    registration_code = models.CharField(max_length=20, default="", blank=True)


class EmailTemp(EntityMixin):
    customer = models.ForeignKey(
        Customer, related_name="email_temp", on_delete=models.CASCADE
    )

    email = models.EmailField(default="")


class OTPTemp(EntityMixin):
    customer = models.ForeignKey(
        Customer, related_name="otp_temp", on_delete=models.CASCADE
    )

    code = models.PositiveSmallIntegerField()


class EmailChange(EntityMixin):
    customer = models.ForeignKey(
        Customer, related_name="email_change", on_delete=models.CASCADE
    )

    old_email = NullableUniqueEmailField(max_length=75, default="", null=True)
    new_email = NullableUniqueEmailField(max_length=75, default="", null=True)


class PhoneChange(EntityMixin):
    customer = models.ForeignKey(
        Customer, related_name="mobile_change", on_delete=models.CASCADE
    )

    old_mobile = NullableUniqueCharField(max_length=15, default="", null=True)
    new_mobile = NullableUniqueCharField(max_length=15, default="", null=True)
