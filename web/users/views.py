from __future__ import unicode_literals
import json

# Django
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect  # , get_object_or_404
from django.views.generic.base import View
from django.views.generic.edit import FormView
from django.utils.decorators import method_decorator


# Local Apps
from .forms import UserProfileForm  # ,LoginForm


def logout_view(request):
    next_url = request.GET.get('next', '/')
    logout(request)
    return redirect(next_url)


# class GuidLoginView(View):
#
#     def get(self, request, guid):
#         login_email = get_object_or_404(LoginEmail, guid=guid, is_used=False)
#
#         login_data = {
#             "email": login_email.user.email,
#             "username": login_email.user.username,
#             "password": settings.SHARED_PASSWORD,
#             "should_create": False
#         }
#         form = LoginForm(login_data)
#         if form.is_valid(request, from_login_email=True):
#             login_email.is_used = True
#             login_email.save()
#             return redirect(form.instance.clan.get_absolute_url())
#         else:
#             messages.add_message(request, messages.WARNING, "We encountered a problem processing this login email.")
#             return redirect("/")


class LoginView(View):

    def post(self, request, *args, **kwargs):
        # Send in raw POST data, falling back to JSON data (available at request.body),
        # falling even further back to an empty dictionary that won't get us very far

        login_data = request.POST or json.loads(request.body) if request.body else {}
        form = LoginForm(login_data)

        if form.is_valid(request):
            return HttpResponse(status=200)
        else:
            if hasattr(form, "instance") and isinstance(form.instance, AnonymousUser):
                # Looks like we received valid, unknown information. Return a 404 so JS
                # knows we should prompt to make a new user.
                return HttpResponse(status=404)
            return JsonResponse(form.errors, status=400)


class OwnProfileView(FormView):
    template_name = "users/profile-edit.html"
    form_class = UserProfileForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(OwnProfileView, self).dispatch(request, *args, **kwargs)

    @property
    def object(self):
        return self.request.user

    def get_form_kwargs(self):
        form_kwargs = super(OwnProfileView, self).get_form_kwargs()
        form_kwargs.update({
            "instance": self.object
        })
        return form_kwargs

    def form_valid(self, form):
        form.save(self.request.user)
        messages.add_message(self.request, messages.SUCCESS, "Profile successfully updated.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("my-profile")
