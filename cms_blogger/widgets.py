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


class ButtonWidget(forms.widgets.CheckboxInput):
    # make it a CheckboxInput in order to not show the ':' after the label

    class Media:
        css = {
            'all': (
                static('cms_blogger/css/redmond-jquery-ui.css'),)
        }
        js = (static('cms_blogger/js/jquery-1.9.1.min.js'),
              static('cms_blogger/js/jquery-ui.min.js'), )

    hide_label = (
        '<style type="text/css">label[for="id_%s"]{'
        'display:none !important;}</style>')

    make_js_button = (
        "<script type='text/javascript'>"
        "jQuery('#id_%s').button().click(function(event) {"
            "event.preventDefault();%s});"
        "</script>")
    submit_on_click_js = (
        "jQuery(this).closest('form').append("
        "jQuery('<input>').attr('type', 'hidden').attr("
            "'name', '_continue').val('Save')"
        ").submit();")

    def __init__(self, attrs=None, check_test=None, link_url='',
                 text=None, submit=False, on_click=''):
        super(ButtonWidget, self).__init__(attrs, check_test)
        self.text = text
        self.link_url = link_url or "#"
        self.submit = submit
        self.on_click = on_click

    def _render_js_on_click(self):
        return "%s%s" % (
            self.on_click, self.submit_on_click_js if self.submit else '')

    def render(self, name, value, attrs=None):
        text = self.text or name.capitalize()
        return mark_safe(
            u"%s<a href='%s' id='id_%s'>%s</a>%s" % (
                self.hide_label % name, self.link_url, name, text,
                self.make_js_button % (name, self._render_js_on_click(), )))

    def value_from_datadict(self, data, files, name):
        return False

    def _has_changed(self, initial, data):
        return False
