from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.utils.safestring import mark_safe
from django.template import Library
from dateutil import tz, relativedelta
import json
import calendar
import datetime
import time


register = Library()


@register.filter
def jsonify(obj_to_jsonify):
    if isinstance(obj_to_jsonify, QuerySet):
        return mark_safe(serialize('json', obj_to_jsonify))
    return mark_safe(json.dumps(obj_to_jsonify))

jsonify.is_safe = True


@register.inclusion_tag('cms_blogger/entry_pub_date.html')
def publish_date_box(entry):
    datetime_obj = entry.publication_date
    is_aware = (datetime_obj.tzinfo is not None and
                datetime_obj.tzinfo.utcoffset(datetime_obj) is not None)
    if is_aware:
        as_utc = datetime_obj.astimezone(tz.tzutc())
    else:
        as_utc = datetime_obj
    as_utc = as_utc.replace(tzinfo=None)
    # entry was published for more than 3 months
    is_older = as_utc < (datetime.datetime.utcnow() +
                         relativedelta.relativedelta(months=-3))
    return {
        'date_var': (
            "entry_pub_%s%s" % (time.time(), entry.id)).replace('.' , ''),
        'utc_millis': calendar.timegm(as_utc.timetuple()) * 1000,
        'show_year': is_older}
