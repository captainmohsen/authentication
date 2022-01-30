from django.db import models


class NullableUniqueCharField(models.CharField):
    description = "CharField that stores NULL but returns ''"

    def to_python(self, value):
        if isinstance(value, models.CharField):
            return value
        return value or ""

    def get_prep_value(self, value):
        return value or None


class NullableUniqueEmailField(models.EmailField):
    description = "EmailField that stores NULL but returns ''"

    def to_python(self, value):
        if isinstance(value, models.EmailField):
            return value
        return value or ""

    def get_prep_value(self, value):
        return value or None
