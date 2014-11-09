from __future__ import unicode_literals
import time
from contextlib import contextmanager

# Django
from django.conf import settings

# Local Apps
from core.utils import smoosh_args


def stopwatch(thing_to_time):
    """
    Decorator usage:
        @stopwatch
        def my_func():
            ...

    Context Manager usage:
        with stopwatch("piece of code"):
            random()
            stuff()
            to()
            time()

        this_stuff_isnt_timed()
    """

    @contextmanager
    def benchmark():
        start = time.time()
        yield
        end = time.time()

        if settings.DEBUG:
            print("%s : %0.3f seconds" % (thing_to_time, end - start))

    if hasattr(thing_to_time, "__call__"):
        def timed(*args, **kwargs):
            with benchmark():
                return thing_to_time(*args, **kwargs)
        return timed
    else:
        return benchmark()


def memoize(fnc):
    """
    Decorator that accepts a variable name at which to cache the results
    of this function. Now honoring parameters!

    Usage:

        class SomeClass(object):
            @memoize
            def get_title(self):
                print "doing work!"
                return "Jurassic Park"

            @property
            @memoize
            def favorite_trilogy(self):
                print "doing property work!"
                return "Star Wars"


        >>> my_obj = SomeClass()
        >>> my_obj.get_title()
        >>> doing work!
        >>> "Jurassic Park"
        >>>
        >>> my_obj.get_title()
        >>> "Jurassic Park"
        >>>
        >>> my_obj.favorite_trilogy
        >>> doing property work!
        >>> "Star Wars"
        >>>
        >>> my_obj.favorite_trilogy
        >>> "Star Wars"

    """
    def wrapper(self, *args, **kwargs):
        # Make sure the memoize cache
        if not hasattr(self, '_memoize_cache'):
            self._memoize_cache = {}

        cache_attr_name = fnc.__name__
        self._memoize_cache.setdefault(cache_attr_name, {})

        key_suffix = smoosh_args(*args, **kwargs)

        try:
            # Hope for a cache hit
            return self._memoize_cache[cache_attr_name][key_suffix]
        except KeyError:
            self._memoize_cache[cache_attr_name][key_suffix] = None

        # Calculate the value
        val = fnc(self, *args, **kwargs)

        # Save it for later
        self._memoize_cache[cache_attr_name][key_suffix] = val
        return val

    return wrapper
