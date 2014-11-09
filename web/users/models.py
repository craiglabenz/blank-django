# Django
from django.contrib.auth.models import AbstractUser

# 3rd Party
from model_utils import FieldTracker

# Local Apps
from .managers import UserManager
from core.models import BaseModel, GeoMixin


class User(GeoMixin, AbstractUser, BaseModel):

    tracker = FieldTracker()
    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.name or self.email

    def get_short_name(self):
        return self.username

    @property
    def name(self):
        return self.get_full_name() or self.get_short_name()

    def as_email_recipient(self):
        if self.name:
            return "{0} <{1}>".format(self.name, self.email)
        else:
            return self.email

    def get_full_name(self):
        return "{0} {1}".format(self.first_name, self.last_name).strip()

    def get_timezone_string(self):
        if self.timezone:
            return self.timezone
        else:
            return ''

    def get_serialization_excludes(self):
        return super(User, self).get_serialization_excludes() + ["is_active", "is_staff", "is_superuser", "password", "date_joined", "timezone", "country"]
