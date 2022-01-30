import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_national_code(value):
    if not re.search(r"^\d{10}$", value):
        raise ValidationError(_("Enter a valid national code"))
    check = int(value[9])
    s = sum(int(value[x]) * (10 - x) for x in range(9)) % 11
    result = check == s if s < 2 else check + s == 11
    if not result:
        raise ValidationError(_("Enter a valid national code"))
