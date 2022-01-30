import logging

from django.conf import settings as django_settings
from django.contrib import auth
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins
from rest_framework import permissions as rf_permissions
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.exceptions import TokenBackendError, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.apps.customer import models, serializers, tasks, utils
from authentication.utils import get_local_time

logger = logging.getLogger(__name__)


class CustomerViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = models.Customer.objects.all()
    serializer_class = serializers.CustomerSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "id"
    http_method_names = ["get", "post", "patch", "head", "options"]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        email_change = models.EmailChange.objects.filter(customer=instance).latest(
            "created_at"
        )
        mobile_change = models.PhoneChange.objects.filter(customer=instance).latest(
            "created_at"
        )
        if email_change.new_email:
            tasks.send_email_verification.delay(instance.username.id.hex)
        if mobile_change.new_mobile:
            tasks.send_mobile_verification_code.delay(instance.username.id)

        return Response(
            serializers.CustomerDetailSerializer(instance=instance).data,
            status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["get"],
    )
    def me(self, request, *args, **kwargs):
        customer = models.Customer.objects.get(id=request.user.id)
        serializer = self.get_serializer(customer)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[rf_permissions.AllowAny],
        authentication_classes=(),
    )
    def signup(self, request):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = serializer.save()
        if contact.email:
            tasks.send_email_verification.delay(contact.id.hex)
        if contact.mobile:
            tasks.send_mobile_verification_code.delay(contact.id)
        return Response(
            serializers.CustomerDetailSerializer(instance=contact.customer).data,
            status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[rf_permissions.AllowAny],
        authentication_classes=(),
    )
    def verify_email(self, request, id=None):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = self.get_object()
        email_change = models.EmailChange.objects.filter(customer=customer).latest(
            "created_at"
        )

        if customer.email_verify:
            return Response(
                {"Success": _("Email already activated")}, status=status.HTTP_200_OK
            )

        temp = customer.email_temp.filter(id=serializer.validated_data["id"])
        if not temp.exists():
            return Response(
                {"Error": _("Email Verification Request Not Found")},
                status.HTTP_400_BAD_REQUEST,
            )

        elif (
            get_local_time() - temp.all()[0].created_at
            > django_settings.AUTHENTICATION_CUSTOMER["EMAIL_VERIFICATION_EXPIRE_TIME"]
        ):
            return Response({"Error": _("Expired")}, status.HTTP_400_BAD_REQUEST)

        customer.email_verify = get_local_time()
        customer.is_active = True
        customer.save()
        if email_change.new_email != "" and email_change.new_email is not None:
            customer.username.email = email_change.new_email
            customer.username.save()
        email_change.new_email = ""
        email_change.save()
        customer.email_temp.all().delete()

        token = self.refresh_token(customer)

        return Response({"token": token}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[rf_permissions.AllowAny],
        authentication_classes=(),
    )
    def resend_email(self, request, id=None):
        customer = self.get_object()

        if customer.email_verify:
            return Response(
                {"Success": "Email already activated"}, status=status.HTTP_200_OK
            )

        if not customer.email_temp.exists():
            return Response(
                {"Error": "You must signup first"}, status=status.HTTP_400_BAD_REQUEST
            )

        temp = customer.email_temp.order_by("-created_at")[0]
        if (
            get_local_time() - temp.created_at
            < django_settings.AUTHENTICATION_CUSTOMER[
                "EMAIL_VERIFICATION_RESEND_TIME_LIMIT"
            ]
        ):
            return Response(
                {
                    "Error": _(
                        f"You must wait {django_settings.AUTHENTICATION_CUSTOMER['EMAIL_VERIFICATION_RESEND_TIME_LIMIT'] -(get_local_time() - temp.created_at)} to request to resend email"
                    )
                },
                status.HTTP_400_BAD_REQUEST,
            )

        tasks.send_email_verification.delay(customer.username.id.hex)

        return Response({"Success": _("Email resent")}, status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[rf_permissions.AllowAny],
        authentication_classes=(),
    )
    def change_email(self, request, id=None):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = self.get_object()

        if customer.email_verify:
            return Response(
                {"Success": "Email already activated"}, status=status.HTTP_200_OK
            )

        if (
            len({temp["email"] for temp in customer.email_temp.values("email")})
            >= django_settings.AUTHENTICATION_CUSTOMER[
                "EMAIL_VERIFICATION_CHANGE_LIMIT"
            ]
        ):
            return Response(
                {"Error": "Max email change request exceeded"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        customer.username.email = serializer.validated_data["email"]
        customer.username.save()

        tasks.send_email_verification.delay(customer.username.id.hex)

        return Response({"Success": _("Email sent")}, status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[rf_permissions.AllowAny],
    )
    def signin(self, request):
        serializer = self.get_serializer_class()(data=request.data)

        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email", None)
        mobile = serializer.validated_data.get("mobile", None)
        # remind_me = serializer.validated_data.get("remind_me", False)

        if django_settings.AUTHENTICATION_CUSTOMER["RECAPTCHA"]["ENABLED"]:
            if not utils.validate_recaptcha(serializer.validated_data["recaptcha"]):
                return Response(
                    data={"detail": _("Wrong Captcha.")},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        username = ""
        if email:
            username = email
        elif mobile:
            username = mobile

        source_ip = request.META.get("REMOTE_ADDR")
        auth_failure_key = "LOGIN_FAILURES_OF_%s_AT_%s" % (username, source_ip)
        auth_failures = cache.get(auth_failure_key) or 0
        lockout_time_in_mins = 10

        if auth_failures >= 4:
            return Response(
                data={
                    "detail": _("Username is locked out. Try in %s minutes.")
                    % lockout_time_in_mins
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        customer = auth.authenticate(
            request=request,
            email=email,
            mobile=mobile,
            password=serializer.validated_data["password"],
        )

        if not customer:
            cache.set(auth_failure_key, auth_failures + 1, lockout_time_in_mins * 60)

            return Response(
                data={"detail": _("Invalid username/password."), "f": auth_failures},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        else:
            cache.delete(auth_failure_key)

        if not customer.is_active:
            logger.debug("Not returning auth token: " "customer %s is disabled", email)
            return Response(
                data={"detail": _("Customer account is disabled.")},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token = self.refresh_token(customer)

        return Response(
            {
                "token": token,
            }
        )

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def signout(self, request):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data.get("refresh", None)
        try:

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"detail": _("Successfull log out.")},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except TokenError or TokenBackendError:
            return Response(
                {"error": _("token is invalid or expired")},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def change_password(self, request, id=None):
        customer = self.get_object()
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not customer.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"old_password": "Incorrect Password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_password = serializer.validated_data["new_password"]
        customer.set_password(new_password)
        customer.save()
        refresh_token = request.data["refresh"]
        try:

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {
                    "detail": _(
                        "Password has been successfully updated and you log out."
                    )
                },
                status=status.HTTP_200_OK,
            )
        except TokenError or TokenBackendError:
            return Response(
                {"error": _("token is invalid or expired")},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"], permission_classes=[rf_permissions.AllowAny])
    def verify_mobile(self, request, id=None):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = self.get_object()
        mobile_change = models.PhoneChange.objects.filter(customer=customer).latest(
            "created_at"
        )

        if customer.mobile_verify:
            return Response(
                {"Success": "Mobile already verified"}, status=status.HTTP_200_OK
            )

        temp = customer.otp_temp.all().order_by("-created_at")

        if (
            get_local_time() - temp[0].created_at
            > django_settings.AUTHENTICATION_CUSTOMER["OTP_EXPIRE_TIME"]
        ):
            return Response({"Error": _("Code expired")}, status.HTTP_400_BAD_REQUEST)

        if serializer.validated_data["code"] == temp[0].code:
            temp.delete()

            customer.mobile_verify = get_local_time()
            customer.is_active = True
            customer.save()
            if mobile_change.new_mobile != "" and mobile_change.new_mobile is not None:
                customer.username.mobile = mobile_change.new_mobile
                customer.username.save()
            mobile_change.new_mobile = ""
            mobile_change.save()

            token = self.refresh_token(customer)

            return Response({"token": token}, status.HTTP_200_OK)

        return Response({"Error": _("Invalid code")}, status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], permission_classes=[rf_permissions.AllowAny])
    def resend_mobile_code(self, request, id=None):
        customer = self.get_object()
        if customer.mobile_verify:
            return Response(
                {"Success": "Mobile already verified"}, status=status.HTTP_200_OK
            )

        temp = customer.otp_temp.all().order_by("-created_at")[0]
        if (
            get_local_time() - temp.created_at
            < django_settings.AUTHENTICATION_CUSTOMER["OTP_EXPIRE_TIME"]
        ):
            return Response(
                {
                    "Error": _(
                        f"You must wait {django_settings.AUTHENTICATION_CUSTOMER['OTP_EXPIRE_TIME'] - (get_local_time() - temp.created_at)} to request to resend code"
                    )
                },
                status.HTTP_400_BAD_REQUEST,
            )

        tasks.send_mobile_verification_code.delay(customer.username.id.hex)
        return Response({"Success": _("Code resent")}, status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[rf_permissions.AllowAny])
    def change_mobile(self, request, id=None):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = self.get_object()

        if customer.mobile_verify:
            return Response(
                {"Success": "Mobile already verified"}, status=status.HTTP_200_OK
            )

        customer.username.mobile = serializer.validated_data["mobile"]
        customer.username.save()

        tasks.send_mobile_verification_code.delay(customer.username.id.hex)

        return Response({"Success": _("Code sent")}, status.HTTP_200_OK)

    def get_serializer_class(self):
        if self.action == "signup":
            return serializers.SignupSerializer
        elif self.action == "signin":
            return serializers.SigninSerializer
        elif self.action == "signout":
            return serializers.SignoutSerializer
        elif self.action == "change_password":
            return serializers.ChangePasswordSerializer
        elif self.action == "change_email":
            return serializers.ChangeEmailSerializer
        elif self.action == "verify_email":
            return serializers.UUIDSerializer
        elif self.action == "verify_mobile":
            return serializers.OTPSerializer
        elif self.action == "change_mobile":
            return serializers.MobileSerializer
        elif self.action == "partial_update":
            return serializers.CustomerUpdateSerializer
        elif self.action == "me":
            return serializers.CustomerDetailSerializer
        return self.serializer_class

    def refresh_token(self, customer):
        refresh = RefreshToken.for_user(customer)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
