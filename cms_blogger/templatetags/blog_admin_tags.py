#-*- coding: utf-8 -*-
from django.template import Library
register = Library()


@register.simple_tag(takes_context=True)
def current_site(context):
    from django.contrib.sites.models import Site
    return Site.objects.get_current()
