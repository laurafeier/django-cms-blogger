#-*- coding: utf-8 -*-
from django.template import Library
register = Library()


@register.simple_tag()
def site_url(site):
    from cms.models import Page
    # cms home page always has url '/'; just fetch the path since it might
    # have overwrite_url
    home_page_path = Page.objects.get_home(site=site).get_path()
    if home_page_path:
        home_page_path = "/%s" % home_page_path
    return "http://%s%s" % (site.domain, home_page_path)


@register.simple_tag(takes_context=True)
def current_site(context):
    from django.contrib.sites.models import Site
    return Site.objects.get_current()
