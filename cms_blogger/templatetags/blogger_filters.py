from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.utils.safestring import mark_safe
from django.template import Library
from dateutil import tz
import json
import calendar

register = Library()


@register.filter
def jsonify(obj_to_jsonify):
    if isinstance(obj_to_jsonify, QuerySet):
        return mark_safe(serialize('json', obj_to_jsonify))
    return mark_safe(json.dumps(obj_to_jsonify))

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
