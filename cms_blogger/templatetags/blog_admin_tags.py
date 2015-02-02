#-*- coding: utf-8 -*-
from django.template import Library
register = Library()


@register.simple_tag(takes_context=True)
def current_site(context):
    from cms_blogger.utils import get_current_site
    opts = context.get('opts')
    model = opts.concrete_model if opts else None
    return get_current_site(context['request'], model)
