from django.contrib import admin
from django.forms import Media
from django.contrib.admin.templatetags.admin_static import static


class AdminHelper(admin.ModelAdmin):

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
        if hasattr(self, 'readonly_in_change_form'):
            readonly_fields = set(ro for ro in self.readonly_fields)
            if obj and obj.pk:
                readonly_fields |= set(self.readonly_in_change_form)
            else:
                for el in self.readonly_in_change_form:
                    readonly_fields.discard(el)
            self.readonly_fields = list(readonly_fields)
        return super(AdminHelper, self).get_readonly_fields(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if not obj and hasattr(self, 'add_form'):
            self.form = self.add_form
            # reset declared_fieldsets
            self.fieldsets = getattr(self, 'add_form_fieldsets', ())
        elif obj and hasattr(self, 'change_form'):
            self.form = self.change_form
            # reset declared_fieldsets
            self.fieldsets = getattr(self, 'change_form_fieldsets', ())
        formCls = super(AdminHelper, self).get_form(request, obj, **kwargs)
        requires_request = getattr(formCls, 'requires_request', False)
        if requires_request:

            class RequestFormClass(formCls):
                def __new__(cls, *args, **kwargs):
                    kwargs.update({"request": request})
                    return formCls(*args, **kwargs)

            return RequestFormClass
        return formCls
