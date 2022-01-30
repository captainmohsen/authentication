from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.utils import get_local_time


class Info(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        data = {
            "name": "Authentication",
            "time": get_local_time(),
            "version": "0.0.1",
            "provider": _("Khallagh Borhan"),
        }
        return Response(data)


class Config(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        all_app_settings = settings.AUTHENTICATION_CUSTOMER

        public_settings = {}

        for setting in settings.PUBLIC_APP_SETTING:
            public_settings.update({setting: all_app_settings.get(setting, None)})

        return Response(public_settings)
