from __future__ import unicode_literals

# Django
from django.conf.urls import url

# Local Apps
from .views import LoginView, logout_view, OwnProfileView

urlpatterns = [
    url(r'^logout/$', logout_view, name="logout"),
    # url(r'^login/(.+)/$', GuidLoginView.as_view(), name="login-with-guid"),
    url(r'^login/$', LoginView.as_view(), name="login"),
    url(r'^me/$', OwnProfileView.as_view(), name="my-profile"),

]
