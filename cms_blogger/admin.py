from django.contrib import admin
from django.contrib.contenttypes.generic import (
    GenericTabularInline, BaseGenericInlineFormSet)
from cms.admin.placeholderadmin import PlaceholderAdmin
from .models import Blog, BlogEntry
from .forms import BlogLayoutForm, BlogForm
from cms_layouts.models import Layout
from django.shortcuts import get_object_or_404
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

    def get_formset(self, request, obj=None, **kwargs):
        formSet = super(BlogLayoutInline, self).get_formset(
            request, obj, **kwargs)
        if obj:
            available_pages = Page.objects.on_site(obj.site)
        else:
            available_pages = Page.objects.get_empty_query_set()
        formSet.form.base_fields['from_page'].queryset = available_pages
        formSet.form.base_fields['from_page'].widget.can_add_related = False
        return formSet

    def layout_customization(self, obj):
        if obj.id:
            opts = self.model._meta
            return "<a href='#' target='_blank'>Customize Layout content</a>"
        else:
            return "(save to customize layout)"
    layout_customization.allow_tags = True


class BlogAdmin(admin.ModelAdmin):
    inlines = [BlogLayoutInline, ]
    form = BlogForm

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = set(ro for ro in self.readonly_fields)
        if obj and obj.pk:
            readonly_fields.add('site')
        else:
            readonly_fields.discard('site')
        self.readonly_fields = list(readonly_fields)
        return super(BlogAdmin, self).get_readonly_fields(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        form = super(BlogAdmin, self).get_form(request, obj, **kwargs)
        if obj and obj.pk:
            return form
        form.base_fields.pop('categories', None)
        return form

    def get_formsets(self, request, obj=None):
        if obj and obj.pk:
            return super(BlogAdmin, self).get_formsets(request, obj)
        return []

    def save_model(self, request, obj, form, change):
        result = super(BlogAdmin, self).save_model(request, obj, form, change)
        if not obj.layouts:
            from cms.models import Page
            cms_home_page = Page.objects.get_home(obj.site)
            default_layout = Layout.objects.create(
                from_page=cms_home_page, layout_type=Blog.ALL,
                content_object=obj)
        return result


class BlogEntryAdmin(PlaceholderAdmin):

    required_fields = ('blog', 'title', 'slug', 'author')

    def get_form(self, request, obj=None, **kwargs):
        form = super(BlogEntryAdmin, self).get_form(request, obj, **kwargs)
        if obj and obj.pk:
            return form
        for field in form.base_fields.keys():
            if field not in self.required_fields:
                form.base_fields.pop(field, None)
        return form

    def edit_plugin(self, request, plugin_id):
        plugin = get_object_or_404(CMSPlugin, pk=int(plugin_id))
        entry = BlogEntry.objects.get(content=plugin.placeholder)
        setattr(request, 'current_page', entry.get_layout().from_page)
        return super(BlogEntryAdmin, self).edit_plugin(request, plugin_id)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [ro for ro in self.readonly_fields]
        if obj and obj.pk and 'blog' not in readonly_fields:
            readonly_fields.append('blog')
        self.readonly_fields = readonly_fields
        return super(BlogEntryAdmin, self).get_readonly_fields(request, obj)


admin.site.register(Blog, BlogAdmin)
admin.site.register(BlogEntry, BlogEntryAdmin)
