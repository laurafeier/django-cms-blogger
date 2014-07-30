from django.contrib import admin
from django.forms import Media, ModelForm
from django.contrib.admin.templatetags.admin_static import static
from collections import namedtuple

CustomForm = namedtuple('CustomForm', 'form fieldsets readonly when')


class AdminHelper(admin.ModelAdmin):

    custom_forms = ()

    def __init__(self, *args, **kwargs):
        super(AdminHelper, self).__init__(*args, **kwargs)
        self._wizard_forms = []
        self._original_readonly_fields = self.readonly_fields

        def from_cls(custom_form, attr):
            val = getattr(custom_form, attr, None)
            if isinstance(val, basestring):
                return getattr(self.__class__, val)
            return val

        for _form in self.custom_forms:
            self._wizard_forms.append(
                CustomForm(**dict(map(lambda f: (f, from_cls(_form, f)),
                                  _form._fields))))
        if self._wizard_forms:
            return

        other_custom_forms = {
            'add': lambda obj: True if not obj else False,
            'change': lambda obj: True if obj else False
        }

        for attr, when in other_custom_forms.items():
            form_attr = '%s_form' % attr
            if not hasattr(self, form_attr):
                continue
            self._wizard_forms.append(
                CustomForm(
                    form=getattr(self, form_attr, None),
                    fieldsets=getattr(self, '%s_fieldsets' % form_attr, None),
                    readonly=getattr(self, 'readonly_in_%s' % form_attr, None),
                    when=when
                ))

    def _upgrade_jquery(self, media):
        # upgrade jquery and cms jquery UI
        new_media = Media()
        new_media.add_css(media._css)

        new_jquery_version = static('cms_blogger/js/jquery-1.9.1.min.js')
        new_jquery_ui_version = static('cms_blogger/js/jquery-ui.min.js')
        # make sure all jquery namespaces point to the same jquery
        jquery_namspace = static('cms_blogger/js/jQuery-patch.js')
        django_jquery_urls = [static('admin/js/jquery.js'),
                              static('admin/js/jquery.min.js')]
        django_collapse_js = [static('admin/js/collapse.js'),
                              static('admin/js/collapse.min.js')]
        for js in media._js:
            if js in django_jquery_urls:
                new_media.add_js((new_jquery_version, ))
            elif js in django_collapse_js:
                new_media.add_js(
                    (static('cms_blogger/js/admin-collapse.js'), ))
            elif js == static('admin/js/jquery.init.js'):
                new_media.add_js((js, jquery_namspace))
            elif js.startswith(static('cms/js/libs/jquery.ui.')):
                new_media.add_js((new_jquery_ui_version, ))
            else:
                new_media.add_js((js, ))
        return new_media

    def get_changelist(self, request, **kwargs):
        if hasattr(self, 'custom_changelist_class'):
            return self.custom_changelist_class
        return super(AdminHelper, self).get_changelist(request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        custom = self._get_wizard_form(obj)
        if custom and custom.readonly:
            self.readonly_fields = list(set(ro for ro in custom.readonly))
        else:
            self.readonly_fields = self._original_readonly_fields
        return super(AdminHelper, self).get_readonly_fields(request, obj)

    def _get_wizard_form(self, obj):
        return next(
            (f for f in self._wizard_forms if f.when(obj)), None)

    def _reset_custom_form(self, request, obj=None, **kwargs):
        custom = self._get_wizard_form(obj)
        if custom:
            self.form = custom.form or ModelForm
            self.fieldsets = custom.fieldsets or ()
        else:
            self.form = ModelForm
            self.fieldsets = ()

    def get_form(self, request, obj=None, **kwargs):
        self._reset_custom_form(request, obj, **kwargs)
        formCls = super(AdminHelper, self).get_form(request, obj, **kwargs)

        requires_request = getattr(formCls, 'requires_request', False)
        if requires_request:

            class RequestFormClass(formCls):

                def __new__(cls, *args, **kwargs):
                    kwargs.update({"request": request})
                    return formCls(*args, **kwargs)

            return RequestFormClass
        return formCls
