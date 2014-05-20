from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.utils.safestring import mark_safe
from django.template import Library
from dateutil import tz
import json, calendar

register = Library()


@register.filter(name="jsonify")
def jsonify(object):
    if isinstance(object, QuerySet):
        return mark_safe(serialize('json', object))
    return mark_safe(json.dumps(object))

jsonify.is_safe = True


@register.filter
def js_date_str(datetime_obj):
    try:
        as_utc = datetime_obj.astimezone(tz.tzutc())
        sec_epoch_utc = calendar.timegm(as_utc.timetuple()) * 1000
        return "new Date(%d)" % sec_epoch_utc
    except AttributeError:
        pass
    return ''
