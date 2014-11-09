# Django
from django.conf import settings as _settings


def settings(request):
    return {"settings": _settings}


def messages(request):
    if hasattr(request, "_messages"):
        messages = request._messages
    else:
        messages = []

    return {"messages": messages}
