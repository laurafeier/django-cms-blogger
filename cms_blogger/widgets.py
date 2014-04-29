from django import forms
from django.utils.safestring import mark_safe
from django.contrib.admin.templatetags.admin_static import static
from dateutil import tz, parser
from django.template.loader import render_to_string
from .settings import (MAXIMUM_THUMBNAIL_FILE_SIZE,
                       ALLOWED_THUMBNAIL_IMAGE_TYPES)


class ToggleWidget(forms.widgets.CheckboxInput):

    class Media:
        css = {
            'all': (
                static('cms_blogger/css/toggle-to-right.css'),
                static('cms_blogger/css/toggles-light.css'),)
        }
        js = (static('cms_blogger/js/jquery-1.9.1.min.js'),
              static('cms_blogger/js/toggles.min.js'),)

    toggle_script = (
        "<script type='text/javascript'> jQuery("
        "function(){jQuery('.toggle_%s').toggles({"
        "checkbox: jQuery('#id_%s'), "
        "height: 30,"
        "width: 65,"
        "on:jQuery('#id_%s').is(':checked')});});</script>")

    toggle_html = (
        '<div class="toggle-light" style="display:inline-block"> '
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
            u"%s<a %s href='%s' id='id_%s'>%s</a>%s" % (
                self.hide_label % name,
                forms.util.flatatt(self.build_attrs(attrs)),
                self.link_url, name, text,
                self.make_js_button % (name, self._render_js_on_click(), )))

    def value_from_datadict(self, data, files, name):
        return False

    def _has_changed(self, initial, data):
        return False


class DateTimeWidget(forms.widgets.TextInput):

    class Media:
        css = {
            'all': (
                static('cms_blogger/css/redmond-jquery-ui.css'),
                static('cms_blogger/css/datetimepicker-extension.css'),
            )
        }
        js = (static('cms_blogger/js/jquery-1.9.1.min.js'),
              static('cms_blogger/js/jquery-ui.min.js'),
              static('cms_blogger/js/jquery-ui-timepicker-addon.js'),
              static('cms_blogger/js/datetimepicker-field.js'),
              static('cms_blogger/js/moment.min.js')
              )

    def render(self, name, value, attrs={}):
        html = (
            u"<input type='text' size='30' name='{name}' id='id_{name}' "
            u"class='ui-button ui-corner-all ui-state-focus ui-textfield'/>"
            u"<div id='picker_id_{name}'></div>"
            u"<script type='text/javascript'>"
            u"buildDatetimePickerField("
            u"'#picker_id_{name}', '#id_{name}', '{initial}');"
            u"</script>"
        )
        return mark_safe(html.format(name=name, initial=value or ''))

    def value_from_datadict(self, data, files, name):
        value = super(DateTimeWidget, self).value_from_datadict(
            data, files, name)
        try:
            date = parser.parse(value).astimezone(tz.tzutc())
        except:
            date = None
        return date


class PosterImage(forms.widgets.CheckboxInput):

    class Media:
        js = (static('filer/js/fileuploader.js'),)

    def render(self, name, value, attrs=None):
        return render_to_string(
            "admin/cms_blogger/blogentrypage/poster_image.html",
            {
                'blog_entry_id': self.blog_entry_id,
                'image_url': self.image_url,
                'size_limit': MAXIMUM_THUMBNAIL_FILE_SIZE,
                'image_types': ALLOWED_THUMBNAIL_IMAGE_TYPES,
            }
        )


class SpinnerWidget(forms.widgets.TextInput):

    class Media:
        css = {
            'all': (
                static('cms_blogger/css/redmond-jquery-ui.css'),
            )
        }
        js = (static('cms_blogger/js/jquery-1.9.1.min.js'),
              static('cms_blogger/js/jquery-ui.min.js'), )

    spinner_script = (
        "<script type='text/javascript'>"
        "jQuery('#id_%s').spinner(%s);"
        "</script>")

    def __init__(self, attrs=None):
        super(SpinnerWidget, self).__init__(attrs=attrs)
        self.spinner_attrs = attrs.pop('spinner', '{}')

    def render(self, name, value, attrs={}):
        widget_html = super(SpinnerWidget, self).render(
            name, value, attrs=attrs)
        output = "%s%s" % (
            widget_html, self.spinner_script % (name, self.spinner_attrs))
        return mark_safe(output)
