from __future__ import unicode_literals

# Django
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.contrib.auth import get_user_model
from django.utils import timezone


class UserManager(DjangoUserManager):
    """
    Custom manager to implement our custom create_user
    and create_superuser methods.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given username.
        """
        if not email:
            raise ValueError('A valid email is required.')

        user = get_user_model()(email=email, **extra_fields)
        if password is not None:
            user.set_password(password)

        # The user has not logged in
        user.last_login = timezone.now()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Creates and saves a superuser User.
        """
        if password is None:
            raise Exception("Must supply a password for new superusers.")

        user = self.create_user(email, password, **extra_fields)
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
