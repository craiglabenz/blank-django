from .base import *  # NOQA

import sys
sys.dont_write_bytecode = True

DEBUG = True


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}


MIDDLEWARE_CLASSES += (
    'core.middleware.LogStuff',
    'core.middleware.TimeRequests',
)

ENV = "local"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(CORE_DIR, 'db.sqlite3'),
    }
}


SITE_PORT = 8000


try:
    from override import *
except ImportError:
    pass
