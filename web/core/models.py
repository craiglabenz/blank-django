import pytz
import uuid

# Django
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.utils import timezone

# 3rd Party
from django_countries.fields import CountryField
from timezone_field import TimeZoneField

# Local
from core.utils import cprint, site_url


TIMEZONE_CHOICES = [(pytz.timezone(tz), tz) for tz in pytz.common_timezones]


class TimezoneMixin(models.Model):
    timezone = TimeZoneField(choices=TIMEZONE_CHOICES, blank=True, null=True)

    class Meta:
        abstract = True

    def get_timezone(self):
        if self.timezone:
            return self.timezone
        else:
            return pytz.UTC

    def get_timezone_string(self):
        tz = self.get_timezone()
        if tz:
            return tz.zone
        else:
            return ''

    def now(self):
        # Get now
        now = timezone.now()

        # Flip it back to naive, which applies the appropriate offset
        naive_now = timezone.make_naive(now, self.get_timezone())

        # Re-apply the timezone which does not apply any offset
        aware_now = timezone.make_aware(naive_now, self.get_timezone())

        return aware_now


class CountryMixin(models.Model):
    country = CountryField(blank=True)

    class Meta:
        abstract = True


class GeoMixin(TimezoneMixin, CountryMixin):

    class Meta:
        abstract = True


class BaseModelMixin(object):

    def __str__(self):
        try:
            return self.as_str()
        except Exception as e:
            if settings.DEBUG:
                cprint("__str__ error {}".format(e), color="red")
            return self.as_str_fallback()

    def as_str_fallback(self):
        if self.pk:
            return '{} Id: {}'.format(self._meta.verbose_name, self.pk)
        else:
            return "Unsaved {}".format(self._meta.verbose_name)

    def as_str(self):
        """
        Classes extending BaseModel are encouraged to implement ``as_str``
        instead of ``__str__`` to prevent any accidental data mismatching
        from ever breaking production functionality.
        """
        name = getattr(self, 'name', None)

        if not name and hasattr(self, 'get_name'):
            name = self.get_name()

        if not name:
            raise ValueError("Could not generate `name` for {}".format(self.as_str_fallback()))

        return name

    @property
    def meta_info(self):
        return (self._meta.app_label, self._meta.model_name,)

    @property
    def admin_view_info(self):
        return '%s_%s' % self.meta_info

    @property
    def admin_uri(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name,), args=(self.pk,))

    @property
    def admin_url(self):
        return site_url(uri=self.admin_uri)

    @classmethod
    def get_content_type(cls):
        return ContentType.objects.get_for_model(cls)

    @classmethod
    def field_names(cls):
        """
        Returns the names of all fields on the model
        """
        return [field.name for field in cls._meta.fields]

    def reload(self):
        """
        In place DB update of the record.
        """
        new_self = self.__class__.objects.get(pk=self.pk)
        self.__dict__.update(new_self.__dict__)
        return self

    def get_field_value(self, field_name, full=False):
        """
        Returns a given value of for this instantiated model.

        Arguments:
        field_name    {string}      The value of the attr you want
        full          {bool}        OPTIONAL. If the passed name is a relation, should it be hydrated?
                                    Defaults to False.
        """
        field = self._meta.get_field(field_name)
        # Is this a related field or a literal?
        if isinstance(field, models.fields.related.RelatedField):
            if full:
                # It's related and they ordered it hydrated
                val = getattr(self, field_name, None)
                # Pull out the value and hydrate it if it exists, else
                # return None
                if val is not None:
                    return val.serialize()  # Don't forward `full` to avoid cyclical problems
                else:
                    return None
            else:
                # Not hydrated is easy enough, just return the PK we
                # already have on hand
                _id = getattr(self, '%s_id' % (field_name,), None)
                serialized = {'id': _id}

                if hasattr(field.related_model, 'add_to_serialization_as_relation'):
                    obj = getattr(self, field.name)
                    if obj:
                        serialized.update(obj.add_to_serialization_as_relation())

                return serialized
                # return _id
        elif isinstance(field, models.fields.DateField):  # Covers both DateTimeField and DateField
            return self._meta.get_field(field_name).value_to_string(self)
        else:
            # Not related? Too easy.
            return getattr(self, field_name, None)

    def append_to_log(self, log, should_save=True, desc=None, should_use_transaction=True,
                      should_reload=True):
        """
        The wrapper function around ``_append_to_log()``. The distinction exists to help
        sanely enforce the ``should_use_transaction`` flag.
        """
        if should_use_transaction:
            with transaction.atomic():
                return self._append_to_log(log, should_save, desc, should_reload)
        else:
            return self._append_to_log(log, should_save, desc, should_reload)

    def _append_to_log(self, log, should_save=True, desc=None, should_reload=True):
        """
        Does the actual work of formatting a log, optional name, and timestamp into
        a block of text that gets appended to the ``self.log``.
        """
        assert 'log' in self.field_names(), "Cannot call ``append_to_log()`` on \
            model without a field named ``log``."

        if self.log is None:
            self.log = ''
            self.save()

        if should_reload:
            # Update local data to ensure sure nothing else committed something
            # to this record before we entered this transaction.
            self.reload()

        pre_log = '##################\n'
        pre_log += '%s\n' % timezone.now().strftime('%b %d, %Y, %I:%M:%S %p UTC')
        if desc:
            pre_log += '**%s**\n' % desc

        post_log = '\n##################\n'

        self.log += '%s%s%s' % (pre_log, log, post_log,)
        if should_save:
            self.save()

        return self


class CacheUUIDModel(models.Model):
    cache_uuid = models.CharField(max_length=36, blank=True, default='', verbose_name="Cache UUID",
                                  help_text="Used as an indicator for when the cached, serialized version of this obj has gone stale.")

    # Called by `self.get_flush_cache_fields()`
    flush_cache_fields = []

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.detect_missing_tracker()

    def detect_missing_tracker(self):
        if not hasattr(self, "tracker"):
            print("Warning! `{}` class inherits from CacheUUIDModel, but lacks a `FieldTracker` attr!".format(type(self).__name__))
            return True
        return False

    def flush_cache_uuid(self, should_save=True):
        self.cache_uuid = str(uuid.uuid4())
        if should_save:
            self.save(should_consider_flushing_cache_uuid=False)

    def should_flush_cache_uuid(self):
        if self.detect_missing_tracker():
            return
        changed_field_names = self.tracker.changed().keys()
        flush_cache_field_name_set = self._get_all_flush_cache_fields()
        return bool(flush_cache_field_name_set.intersection(changed_field_names))

    def _get_all_flush_cache_fields(self):
        """
        The super() version of this function no one should touch.
        Inheriting classes should implement `get_flush_cache_fields()` for their
        model-specific field names.

        @returns    :list:  List of field_name values (strings) that, when changed,
                            flush the cache value of this obj.
        """
        return set(self._get_core_flush_cache_fields() + self.get_flush_cache_fields())

    def _get_core_flush_cache_fields(self):
        """
        Returns the list of field names that ubiquitously result in a cache bust.
        None at this writing, but could foresee a global, changing column one day
        entering this list.
        """
        return []

    def get_flush_cache_fields(self):
        """
        Inheriting classes could implement this.
        """
        return self.flush_cache_fields

    def save(self, **kwargs):
        if kwargs.pop('should_consider_flushing_cache_uuid', True) and self.should_flush_cache_uuid():
            self.flush_cache_uuid(should_save=False)

        self.ensure_cache_uuid()
        super().save(**kwargs)

    def ensure_cache_uuid(self):
        self.cache_uuid = self.cache_uuid or str(uuid.uuid4())


class BaseModel(BaseModelMixin, models.Model):

    # Bookkeeping
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    serialization_excludes = ["created_at", "updated_at"]

    class Meta:
        abstract = True
