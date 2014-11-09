import datetime
import logging
import re
import requests as _requests
import socket
import termcolor
import time

# Django
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

# 3rd Party
try:
    from termcolor import _cprint
except ImportError:
    def _cprint(msg, *args, **kwargs):
        print(msg)


def cprint(msg, *args, **kwargs):
    if settings.TESTING:
        return

    if settings.DEBUG:
        _cprint(msg, *args, **kwargs)
    else:
        pass
        # logger.debug


def site_url(uri='', subdomain=''):
    """
    Handles the fact that ports are annoying.
    """
    if subdomain:
        subdomain = subdomain + '.'

    if settings.SITE_PORT in ['80', '443']:
        return '%s://%s%s%s' % (settings.SITE_PROTOCOL, subdomain, settings.SITE_HOST, uri,)
    else:
        return '%s://%s%s:%s%s' % (settings.SITE_PROTOCOL, subdomain, settings.SITE_HOST, settings.SITE_PORT, uri,)


class requests(object):

    @staticmethod
    def get(*args, **kwargs):
        kwargs['method'] = 'get'
        return requests._requests(*args, **kwargs)

    @staticmethod
    def post(*args, **kwargs):
        kwargs['method'] = 'post'
        return requests._requests(*args, **kwargs)

    @staticmethod
    def put(*args, **kwargs):
        kwargs['method'] = 'put'
        return requests._requests(*args, **kwargs)

    @staticmethod
    def patch(*args, **kwargs):
        kwargs['method'] = 'patch'
        return requests._requests(*args, **kwargs)

    @staticmethod
    def delete(*args, **kwargs):
        kwargs['method'] = 'delete'
        # Option for doing stuff here. Deletes are crazy -- super log them?
        return requests._requests(*args, **kwargs)

    @staticmethod
    def _requests(*args, **kwargs):
        method = kwargs.pop('method', 'get')
        _method = getattr(_requests, method)

        url = args[0]

        # Let's log this for now; if the traffic gets high we can turn it down.
        logger = logging.getLogger('core.utils.requests._requests')
        logger.debug('Beginning %s to %s' % (method, url,))

        if settings.DEBUG or settings.TESTING:
            print_stmt = '%s %s' % (termcolor.colored(method.upper(), color='green'), url,)

        st = time.time()
        try:
            resp = _method(*args, **kwargs)
        except _requests.exceptions.Timeout:
            error_time_ms = '%.3f' % ((time.time() - st) * 1000)
            logger.error('%s %s TIMED OUT after %s ms' % (method.upper(), url, error_time_ms,))
            raise

        resp_time = '%.3f' % ((time.time() - st) * 1000)
        if settings.DEBUG or settings.TESTING:
            print('%s -- Responded in {} ms'.format(print_stmt, colored_resp_time(resp_time),))

        logger.debug('%s %s -- Took %s ms', method.upper(), url, resp_time,)

        return resp


def colored_resp_time(resp_time):
    """
    For stdout (either management commands or the dev server). Colors the
    supplied `resp_time` based on rules of speed.

    Args:
    @resp_time   int    The milliseconds it took for some request to come back.
    """
    resp_time = round(float(resp_time), 3)
    if resp_time < 200.0:
        color = 'green'
    elif resp_time < 500.0:
        color = 'yellow'
    else:
        color = 'red'
    return termcolor.colored(resp_time, color=color)


class RFC5424Filter(logging.Filter):

    """
    Adds a properly formatted time for use in syslog logging. Also adds the
    hostname and the local application name. The application name is used by
    rsyslog routing rules to get log messages to the right files.
    """

    def __init__(self, *args, **kwargs):
        self._tz_fix = re.compile(r'([+-]\d{2})(\d{2})$')
        super(RFC5424Filter, self).__init__(*args, **kwargs)

    def filter(self, record):
        try:
            record.hostname = socket.gethostname()
        except:
            record.hostname = '-'

        # This is here to avoid importing settings within the settings file
        from django.conf import settings
        record.app_name = 'sp-%s-%s' % (settings.APP_ENVIRONMENT, settings.NODE_TYPE)

        isotime = datetime.datetime.fromtimestamp(record.created).isoformat()
        tz = self._tz_fix.match(time.strftime('%z'))
        if time.timezone and tz:
            (offset_hrs, offset_min) = tz.groups()
            isotime = '{0}{1}:{2}'.format(isotime, offset_hrs, offset_min)
        else:
            isotime = isotime + 'Z'

        record.isotime = isotime

        return True


def smoosh_args(*args, **kwargs):
    key_suffix = ''
    prepared_args = []
    prepared_kwargs = []
    for arg in args:
        prepared_args.append(str(arg))

    for key, value in kwargs.items():
        prepared_kwargs.append('%s=%s' % (key, str(value),))

    all_prepared_args = prepared_args + prepared_kwargs
    if all_prepared_args:
        key_suffix = ';'.join(all_prepared_args)

    return key_suffix


class ContentTypeRepo(object):
    _instance = None
    ct_map = {}

    def __new__(cls, *args, **kwargs):
        """
        Singleton implementation
        """
        if not cls._instance:
            cls._instance = super(ContentTypeRepo, cls).__new__(cls, *args, **kwargs)
            cls._instance.seed_ct_map()
        return cls._instance

    def seed_ct_map(self):
        self.ct_map = {}
        for ct in ContentType.objects.all():
            self._instance.ct_map[ct.pk] = ct

    def get_content_type_by_id(self, id):
        return self.ct_map[id]

    def get_class_by_id(self, id):
        return self.get_content_type_by_id(id).model_class()


def valid_content_types():
    """
    Returns an iterator of only valid content types, using the ContentType
    lookup singleton above.
    """
    for pk, ct in ContentTypeRepo().ct_map.items():
        if bool(ct.model_class()):
            yield ct
