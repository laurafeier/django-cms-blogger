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


@register.inclusion_tag('admin/prepopulated_fields_js.html', takes_context=True)
def initial_empty_prepopulated_fields_js(context):
    """
    Follows the logic of the prepopulated_fields_js template tag but it works
    only for forms that have the prepopulated fields with no initial value.
    """
    if not 'adminform' in context:
        return context

    prepopulated_fields = []
    for field_and_deps in context['adminform'].prepopulated_fields:
        field = field_and_deps.get('field')
        if field and not field.value():
            prepopulated_fields.append(field_and_deps)
    context.update({'prepopulated_fields': prepopulated_fields})
    return context
