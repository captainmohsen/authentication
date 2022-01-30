import uuid

from django.db import models
from django.utils import timezone

from authentication.utils import get_local_time


class UUIDMixin(models.Model):
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )

    class Meta:
        abstract = True


class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(default=get_local_time)

    updated_at = models.DateTimeField(default=get_local_time)

    deleted_at = models.DateTimeField(null=True, default=None)

    class Meta:
        abstract = True


class EntityMixin(UUIDMixin, TimeStampMixin):

    # objects = ExcludeDeletedEntityManager()
    # all_objects = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.id:
            self.updated_at = timezone.localtime(timezone.now())
        super(TimeStampMixin, self).save(*args, **kwargs)

    # def delete(self, using=None, keep_parents=False):
    #     self.deleted_at = get_local_time()
    #     self.save()
