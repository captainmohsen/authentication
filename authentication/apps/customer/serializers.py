from django.conf import settings
from django.core import validators
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from authentication.apps.customer import models
from authentication.apps.customer.validators import validate_national_code


class SignupSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=75,
        required=False,
        error_messages={
            "max_length": _("Enter a valid email address"),
            "invalid": _("Enter a valid email address"),
        },
        validators=[
            UniqueValidator(
                queryset=models.Contact.objects.all(),
                message=_("This email already used"),
            ),
        ],
    )

    mobile = serializers.CharField(
        max_length=15,
        required=False,
        validators=[
            validators.RegexValidator(
                r"^(?:0|98|\+98|\+980|0098|098|00980)?(9\d{9})$",
                _("Enter a valid mobile"),
                "invalid",
            ),
            UniqueValidator(
                queryset=models.Contact.objects.all(),
                message=_("This mobile number already used"),
            ),
        ],
        error_messages={
            "max_length": _("Enter a valid mobile"),
            "invalid": _("Enter a valid mobile"),
        },
    )

    national_code = serializers.CharField(
        max_length=10,
        validators=[
            validate_national_code,
            UniqueValidator(
                queryset=models.People.objects.all(),
                message=_("This national code already used"),
            ),
        ],
        error_messages={
            "invalid": _("Enter a valid national code"),
        },
    )

    agree_with_policy = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if not attrs.get("mobile", None) and not attrs.get("email", None):
            raise ValidationError(_("Either mobile or email must be supplied"))
        if attrs.get("mobile", None) and attrs.get("email", None):
            raise ValidationError(_("Just use one of email or mobile"))
        if not attrs.get("agree_with_policy", False):
            raise ValidationError(
                {"agree_with_policy": [_("User must agree with policy to register")]}
            )
        return attrs

    class Meta:
        model = models.Customer
        fields = (
            "email",
            "national_code",
            "mobile",
            "password",
            "agree_with_policy",
        )

    def create(self, validated_data):
        validated_data.pop("agree_with_policy", None)

        people = models.People.objects.create(
            national_code=validated_data.pop("national_code", None)
        )
        contact = models.Contact.objects.create(
            email=validated_data.pop("email", None),
            mobile=validated_data.pop("mobile", None),
            owner=people,
        )
        models.Customer.objects.create_customer(
            contact, password=validated_data.pop("password", ""), owner=people
        )
        models.EmailChange.objects.create(customer=contact.customer)
        models.PhoneChange.objects.create(customer=contact.customer)

        return contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Contact
        fields = (
            "email",
            "mobile",
        )


class EmailChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EmailChange
        fields = (
            "old_email",
            "new_email",
        )


class MobileChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PhoneChange
        fields = (
            "old_mobile",
            "new_mobile",
        )


class PeopleSerilizer(serializers.ModelSerializer):
    class Meta:
        model = models.People
        fields = (
            "name",
            "last_name",
            "national_code",
        )


class CustomerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Customer
        fields = (
            "url",
            "is_active",
            "email_verify",
            "mobile_verify",
            "total_credit",
        )
        extra_kwargs = {
            "url": {"lookup_field": "id", "view_name": "customer-detail"},
        }


class CustomerDetailSerializer(serializers.ModelSerializer):
    contact = ContactSerializer(source="username")
    people = serializers.SerializerMethodField(method_name="get_owner")
    email_change = serializers.SerializerMethodField(method_name="get_change_email")
    mobile_change = serializers.SerializerMethodField(method_name="get_change_mobile")

    def get_owner(self, obj):
        return PeopleSerilizer(instance=obj.people.all()[0]).data

    def get_change_email(self, obj):
        return EmailChangeSerializer(
            instance=obj.email_change.latest("created_at")
        ).data

    def get_change_mobile(self, obj):
        return MobileChangeSerializer(
            instance=obj.mobile_change.latest("created_at")
        ).data

    class Meta:
        model = models.Customer
        fields = (
            "id",
            "is_active",
            "email_verify",
            "mobile_verify",
            "total_credit",
            "contact",
            "people",
            "email_change",
            "mobile_change",
        )


class CustomerUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=75,
        required=False,
        error_messages={
            "max_length": _("Enter a valid email address"),
            "invalid": _("Enter a valid email address"),
        },
        validators=[
            UniqueValidator(
                queryset=models.Contact.objects.all(),
                message=_("This email already used"),
            ),
        ],
    )

    mobile = serializers.CharField(
        max_length=15,
        required=False,
        validators=[
            validators.RegexValidator(
                r"^(?:0|98|\+98|\+980|0098|098|00980)?(9\d{9})$",
                _("Enter a valid mobile"),
                "invalid",
            ),
            UniqueValidator(
                queryset=models.Contact.objects.all(),
                message=_("This mobile number already used"),
            ),
        ],
        error_messages={
            "max_length": _("Enter a valid mobile"),
            "invalid": _("Enter a valid mobile"),
        },
    )

    national_code = serializers.CharField(
        max_length=10,
        required=False,
        validators=[
            validate_national_code,
            UniqueValidator(
                queryset=models.People.objects.all(),
                message=_("This national code already used"),
            ),
        ],
        error_messages={
            "invalid": _("Enter a valid national code"),
        },
    )
    name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    def validate(self, attrs):
        return attrs

    class Meta:
        model = models.Customer
        fields = (
            "email",
            "national_code",
            "mobile",
            "name",
            "last_name",
        )

    def update(self, instance, validated_data):
        if "email" in validated_data:
            instance.email_verify = None
            instance.save()
            models.EmailChange.objects.create(
                customer=instance,
                new_email=validated_data.pop("email", instance.username.email),
                old_email=instance.username.email,
            )

        if "mobile" in validated_data:
            instance.mobile_verify = None
            instance.save()
            models.PhoneChange.objects.create(
                customer=instance,
                new_mobile=validated_data.pop("mobile", instance.username.mobile),
                old_mobile=instance.username.mobile,
            )
        instance.owner.name = validated_data.get("name", instance.owner.name)
        instance.owner.last_name = validated_data.get(
            "last_name", instance.owner.last_name
        )
        instance.owner.national_code = validated_data.get(
            "national_code", instance.owner.national_code
        )
        instance.owner.save()
        return instance


class UUIDSerializer(serializers.Serializer):
    id = serializers.UUIDField()


class ChangeEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(
        max_length=75,
        required=False,
        error_messages={
            "max_length": _("Enter a valid email address"),
            "invalid": _("Enter a valid email address"),
        },
        validators=[
            UniqueValidator(
                queryset=models.Contact.objects.all(),
                message=_("This email already used"),
            ),
        ],
    )


class SigninSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    mobile = serializers.CharField(
        required=False,
        validators=[
            validators.RegexValidator(
                r"^(?:0|98|\+98|\+980|0098|098|00980)?(9\d{9})$",
                _("Enter a valid mobile"),
                "invalid",
            )
        ],
    )
    password = serializers.CharField()
    recaptcha = serializers.CharField(required=False)
    remind_me = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        if settings.AUTHENTICATION_CUSTOMER["RECAPTCHA"]["ENABLED"]:
            if not attrs.get("recaptcha", None):
                raise ValidationError({"recaptcha": [_("Recaptcha required")]})
        if not attrs.get("mobile", None) and not attrs.get("email", None):
            raise ValidationError(_("Either mobile or email must be supplied"))
        if attrs.get("mobile", None) and attrs.get("email", None):
            raise ValidationError(_("Just use one of email or mobile"))

        return attrs


class SignoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class OTPSerializer(serializers.Serializer):
    code = serializers.IntegerField(max_value=9999, min_value=1000)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        min_length=8,
        validators=[
            RegexValidator(
                regex=r"\d",
                message=_("Ensure this field has at least one digit."),
            ),
            RegexValidator(
                regex="[a-zA-Z]",
                message=_("Ensure this field has at least one latin letter."),
            ),
        ],
    )

    confirm_password = serializers.CharField(required=True)
    refresh = serializers.CharField()

    def validate(self, attrs):
        if attrs.get("new_password") == attrs.get("old_password"):
            raise serializers.ValidationError(_("new password same as old password."))
        if attrs.get("confirm_password") != attrs.get("new_password"):
            raise serializers.ValidationError(
                _("new password is not same as confirm password.")
            )
        return attrs


class MobileSerializer(serializers.Serializer):
    mobile = serializers.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                r"^(?:0|98|\+98|\+980|0098|098|00980)?(9\d{9})$",
                _("Enter a valid mobile"),
                "invalid",
            ),
            UniqueValidator(
                queryset=models.Contact.objects.all(),
                message=_("This mobile number already used"),
            ),
        ],
        error_messages={
            "max_length": _("Enter a valid mobile"),
            "invalid": _("Enter a valid mobile"),
        },
    )
