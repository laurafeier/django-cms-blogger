from django.contrib import admin
from django.db import models
from django.contrib.contenttypes.generic import (
    GenericTabularInline, BaseGenericInlineFormSet)
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from cms.admin.placeholderadmin import PlaceholderAdmin
from .models import Blog, BlogEntryPage
from .forms import (
    BlogLayoutForm, BlogForm, BlogAddForm, BlogEntryPageAddForm,
    BlogEntryPageChangeForm)
from .widgets import ToggleWidget
from cms_layouts.models import Layout
from cms.models import Page, CMSPlugin


class BlogLayoutInlineFormSet(BaseGenericInlineFormSet):


    def clean(self):
        # TODO validation for layout types
        pass


class BlogLayoutInline(GenericTabularInline):
    form = BlogLayoutForm
    readonly_fields = ('layout_customization', )
    model = Layout
    extra = 0
    max_num = len(Blog.LAYOUTS_CHOICES.items())
    formset = BlogLayoutInlineFormSet
    description = 'TODO help text'

    def get_formset(self, request, obj=None, **kwargs):
        formSet = super(BlogLayoutInline, self).get_formset(
            request, obj, **kwargs)
        # show one form if there are no layouts
        if obj and obj.layouts.count() == 0:
            formSet.extra = 1
        else:
            formSet.extra = 0

        if obj:
            available_pages = Page.objects.on_site(obj.site)
        else:
            available_pages = Page.objects.get_empty_query_set()
        page_field = formSet.form.base_fields['from_page']
        page_field.queryset = available_pages
        page_field.widget.can_add_related = False
        return formSet

    def layout_customization(self, obj):
        if obj.id:
            pattern = 'admin:%s_%s_change' % (obj._meta.app_label,
                                              obj._meta.module_name)
            url = reverse(pattern,  args=[obj.id])
            url_tag = ("<a href='%s' target='_blank'>Customize Layout "
                       "content</a>" % url)
            return url_tag
        else:
            return "(save to customize layout)"
    layout_customization.allow_tags = True


class CustomAdmin(admin.ModelAdmin):

    def get_readonly_fields(self, request, obj=None):
        if hasattr(self, 'readonly_in_change_form'):
            readonly_fields = set(ro for ro in self.readonly_fields)
            if obj and obj.pk:
                readonly_fields |= set(self.readonly_in_change_form)
            else:
                for el in self.readonly_in_change_form:
                    readonly_fields.discard(el)
            self.readonly_fields = list(readonly_fields)
        return super(CustomAdmin, self).get_readonly_fields(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if not obj and hasattr(self, 'add_form'):
            return self.add_form
        return super(CustomAdmin, self).get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        if hasattr(self, 'change_form_fieldsets'):
            if obj and obj.pk:
                self.fieldsets = self.change_form_fieldsets
            else:
                self.fieldsets = getattr(self, 'add_form_fieldsets', ())
        return super(CustomAdmin, self).get_fieldsets(request, obj)


class BlogAdmin(CustomAdmin):
    inlines = [BlogLayoutInline, ]
    add_form = BlogAddForm
    form = BlogForm
    change_form_template = 'admin/cms_blogger/blog_change_form.html'
    search_fields = ['title', 'site__name']
    list_display = ('title', 'slug', 'site')
    readonly_in_change_form = ['site', ]
    formfield_overrides = {
        models.BooleanField: {'widget': ToggleWidget}
    }
    change_form_fieldsets = (
        ('Blog setup', {
            'fields': ['site', 'title', 'slug', 'entries_slugs_with_date'],
            'classes': ('extrapretty', ),
            'description': 'TODO description'
        }),
        ('Categories', {
            'fields': ['categories'],
            'classes': ('extrapretty', ),
        }),
        ('Social media and commentig integration', {
            'fields': ['enable_facebook', 'enable_twitter'],
            'classes': ('collapse', 'extrapretty', )
        }),
        ('Disqus commentig integration', {
            'fields': ['enable_disqus', 'disqus_shortname',
                       'disable_disqus_for_mobile'],
            'classes': ('wide', 'extrapretty', ),
            'description': 'TODO description'
        }),
    )
    prepopulated_fields = {"slug": ("title",)}

    def get_formsets(self, request, obj=None):
        # don't show layout inline in add view
        if obj and obj.pk:
            return super(BlogAdmin, self).get_formsets(request, obj)
        return []


class BlogEntryPageAdmin(CustomAdmin, PlaceholderAdmin):
    list_display = ('__str__', 'slug', 'blog')
    search_fields = ('title', 'blog__title')
    add_form_template = 'admin/cms_blogger/entry_add_form.html'
    change_form_template = 'admin/cms_blogger/entry_change_form.html'
    add_form = BlogEntryPageAddForm
    form = BlogEntryPageChangeForm
    readonly_in_change_form = ['blog', ]
    change_form_fieldsets = (
        (None, {
            'fields': [
                'title', 'blog', ('slug', 'creation_date'), 'author',
                'abstract', 'body', ('is_published', 'start_publication',
                'end_publication'), 'meta_description',
                'meta_keywords'],
        }),)

    def get_prepopulated_fields(self, request, obj=None):
        if obj and obj.pk:
            self.prepopulated_fields = {"slug": ("title",)}
        else:
            self.prepopulated_fields = {}
        return super(BlogEntryPageAdmin, self).get_prepopulated_fields(request, obj)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = set(ro for ro in self.readonly_fields)
        if obj and obj.blog and not obj.blog.entries_slugs_with_date:
            readonly_fields.add('creation_date')
        else:
            readonly_fields.discard('creation_date')
        self.readonly_fields = list(readonly_fields)
        return super(BlogEntryPageAdmin, self).get_readonly_fields(request, obj)

    def add_plugin(self, request):
        # sice there is no placeholder displayed in the change form, plugins
        #   will be added by passing a parent_id to this view. parent_id
        #   parameter will hold the blog entry id. We need to replace
        #   the parent_id with the text plugin_id in order for the placeholder
        #   admin add_plugin view to work
        post_data = request.POST.copy()
        if 'parent_id' in post_data:
            entry = get_object_or_404(BlogEntryPage, pk=post_data['parent_id'])
            post_data['parent_id'] = entry.get_attached_plugin().pk
            request.POST = post_data
        return super(BlogEntryPageAdmin, self).add_plugin(request)

    def edit_plugin(self, request, plugin_id):
        plugin = get_object_or_404(CMSPlugin, pk=plugin_id)
        entry = BlogEntryPage.objects.get(content=plugin.placeholder)
        setattr(request, 'current_page', entry.get_layout().from_page)
        return super(BlogEntryPageAdmin, self).edit_plugin(request, plugin_id)


admin.site.register(Blog, BlogAdmin)
admin.site.register(BlogEntryPage, BlogEntryPageAdmin)
