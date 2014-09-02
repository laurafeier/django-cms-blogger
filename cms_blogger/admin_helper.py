from django.contrib import admin
from django.forms import Media, ModelForm
from django.contrib.admin.templatetags.admin_static import static
from collections import namedtuple

_wizard_opts = namedtuple(
    'WizardForm', 'form fieldsets readonly prepopulated when show_next')


class WizardForm(_wizard_opts):

    def __new__(cls, form=None, fieldsets=None,
                readonly=None, prepopulated=None, when=None, show_next=False):
        if when is None:
            when = lambda x: False
        return super(WizardForm, cls).__new__(cls,
            form or ModelForm, fieldsets or (), readonly or (),
            prepopulated or {}, when, show_next)


class AdminHelper(admin.ModelAdmin):

    wizard_forms = ()

    def __init__(self, *args, **kwargs):
        super(AdminHelper, self).__init__(*args, **kwargs)
        self._wizard_forms = []

        def lazy_attr(cls, val):
            if isinstance(val, basestring):
                return getattr(cls, val)
            return val

        admin = self.__class__

        for _form in self.wizard_forms:
            get_val = lambda field_name: getattr(_form, field_name)
            as_property = lambda field: (field,
                                         lazy_attr(admin, get_val(field)))
            self._wizard_forms.append(
                WizardForm(**dict(map(as_property, _form._fields))))
        if self._wizard_forms:
            return

        other_wizard_forms = (
            ('add', lambda obj: True if not obj else False),
            ('change', lambda obj: True if obj else False)
        )

        for attr, when in other_wizard_forms:
            form_attr = '%s_form' % attr
            if not hasattr(self, form_attr):
                continue
            self._wizard_forms.append(
                WizardForm(
                    form=getattr(self, form_attr, None),
                    fieldsets=getattr(self, '%s_fieldsets' % form_attr, None),
                    readonly=getattr(
                        self, 'readonly_in_%s' % form_attr, None),
                    prepopulated=getattr(
                        self, 'prepopulated_in_%s' % form_attr, None),
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
        return getattr(
            self, 'custom_changelist_class',
            super(AdminHelper, self).get_changelist(request, **kwargs))

    def get_readonly_fields(self, request, obj=None):
        if self._is_wizard_like():
            custom = self._get_wizard_form(obj) or WizardForm()
            self.readonly_fields = list(set(ro for ro in custom.readonly))
        return super(AdminHelper, self).get_readonly_fields(request, obj)

    def get_prepopulated_fields(self, request, obj=None):
        if self._is_wizard_like():
            custom = self._get_wizard_form(obj) or WizardForm()
            self.prepopulated_fields = dict(custom.prepopulated)
        return super(AdminHelper, self).get_prepopulated_fields(request, obj)

    def _is_wizard_like(self):
        return len(self._wizard_forms) > 0

    def _get_wizard_form(self, obj):
        return next((f for f in self._wizard_forms if f.when(obj)), None)

    def _reset_custom_form(self, request, obj=None, **kwargs):
        custom = self._get_wizard_form(obj) or WizardForm()
        self.form = custom.form
        setattr(self.form, 'show_next_button', custom.show_next)
        self.fieldsets = tuple(custom.fieldsets)

    def get_form(self, request, obj=None, **kwargs):
        if self._is_wizard_like():
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
