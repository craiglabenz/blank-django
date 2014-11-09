from __future__ import unicode_literals

# Django
from django import forms
from django.utils.translation import ugettext_lazy as _

# Local Apps
from .models import User


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "timezone", "country")

        help_texts = {
            "first_name": _("If provided, this information will be public."),
            "last_name": _("If provided, this information will be public."),
            "email": _("If provided, this information will *never* be made public."),
        }
