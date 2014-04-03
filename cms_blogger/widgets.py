from django import forms
from django.utils.safestring import mark_safe
from django.contrib.admin.templatetags.admin_static import static

class ToggleWidget(forms.widgets.CheckboxInput):

    class Media:
        css = {
            'all': (
                static('cms_blogger/css/toggle-to-right.css'),
                static('cms_blogger/css/toggles-modern.css'),)
        }
        js = (static('cms_blogger/js/jquery-1.9.1.min.js'),
              static('cms_blogger/js/toggles.min.js'),)

    toggle_script = (
        "<script type='text/javascript'> jQuery("
        "function(){jQuery('.toggle_%s').toggles({"
        "checkbox: jQuery('#id_%s'), "
        "on:jQuery('#id_%s').is(':checked')});});</script>")

    toggle_html = (
        '<div class="toggle-modern" style="display:inline-block"> '
        '<div class="toggle_%s toggle-select" data-type="select"> '
        '</div></div>%s %s')

    def render(self, name, value, attrs={}):
        attrs.update({'class': 'toggle', 'style': 'display:none'})
        widget_html = super(ToggleWidget, self).render(
            name, value, attrs=attrs)
        output = self.toggle_html % (
            name, widget_html, self.toggle_script % ((name,) * 3))
        return mark_safe(output)


class TagItWidget(forms.widgets.TextInput):

    class Media:
        css = {
            'all': (
                static('cms_blogger/css/redmond-jquery-ui.css'),
                static('cms_blogger/css/jquery.tagit.css'),)
        }
        js = (static('cms_blogger/js/jquery-1.9.1.min.js'),
              static('cms_blogger/js/jquery-ui.min.js'),
              static('cms_blogger/js/tag-it.js'),)

    tagit_script = (
        "<script type='text/javascript'>"
        "jQuery('#id_%s').tagit(%s);"
        "</script>")

    def __init__(self, attrs=None):
        super(TagItWidget, self).__init__(attrs=attrs)
        self.tagit_attrs = attrs.pop('tagit', '{}')

    def render(self, name, value, attrs={}):
        widget_html = super(TagItWidget, self).render(
            name, value, attrs=attrs)
        output = "%s%s" % (
            widget_html, self.tagit_script % (name, self.tagit_attrs))
        return mark_safe(output)
