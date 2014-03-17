from django import forms
from django.utils.safestring import mark_safe


class ToggleWidget(forms.widgets.CheckboxInput):

    class Media:
        css = {
            'all': (
                'cms_blogger/css/toggle-to-right.css',
                'cms_blogger/css/toggles-modern.css',)
        }
        js = ('cms_blogger/js/jquery-1.9.1.min.js',
              'cms_blogger/js/toggles.min.js',)

    toggle_script = (
        "<script> jQuery("
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
