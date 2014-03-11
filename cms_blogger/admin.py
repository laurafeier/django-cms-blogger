from django.contrib import admin
from django.contrib.contenttypes.generic import (
    GenericTabularInline, BaseGenericInlineFormSet)
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from cms.admin.placeholderadmin import PlaceholderAdmin
from cms.utils import get_language_from_request
from .models import Blog, BlogEntry
from .forms import (
    BlogLayoutForm, BlogForm, BlogAddForm, BlogEntryAddForm,
    BlogEntryChangeForm)
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


class BlogAdmin(CustomAdmin):
    inlines = [BlogLayoutInline, ]
    add_form = BlogAddForm
    form = BlogForm
    search_fields = ['title', 'site__name']
    list_display = ('title', 'slug', 'site')
    readonly_in_change_form = ['site', ]

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


class BlogEntryAdmin(PlaceholderAdmin, CustomAdmin):
    list_display = ('__str__', 'slug', 'pretty_blog')
    search_fields = ('title', 'blog__title')
    add_form_template = 'admin/cms_blogger/entry_add_form.html'
    add_form = BlogEntryAddForm
    form = BlogEntryChangeForm
    readonly_in_change_form = ['blog',]
    change_form_fieldsets = (
        (None, {
            'fields': [
                'title', 'blog', 'slug', 'creation_date', 'author',
                'abstract', 'body', 'start_publication',
                'end_publication', 'is_published', 'meta_description',
                'meta_keywords'],
        }),)

    def pretty_blog(self, obj):
        return "%s - %s" % (obj.blog, obj.blog.site)

    def get_form(self, request, obj=None, **kwargs):
        if not obj:
            return self.add_form
        return super(BlogEntryAdmin, self).get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        super(BlogEntryAdmin, self).save_model(request, obj, form, change)
        if not change:
            if obj.content and obj.content.pk and not obj.content.get_plugins():
                from cms.api import add_plugin
                language = get_language_from_request(request)
                add_plugin(obj.content, 'TextPlugin', 'en',
                           body='Add text HERE!!')
        else:
            text_plugin = obj.get_text_instance()
            text_plugin.body = form.cleaned_data['body']
            text_plugin.save()

    def add_plugin(self, request):
        # sice there is no placeholder displayed in the change form, plugins
        #   will be added by passing a parent_id to this view. parent_id
        #   parameter will hold the blog entry id. We need to replace
        #   the parent_id with the text plugin_id in order for the placeholder
        #   admin add_plugin view to work
        post_data = request.POST.copy()
        if 'parent_id' in post_data:
            entry = get_object_or_404(BlogEntry, pk=post_data['parent_id'])
            post_data['parent_id'] = entry.get_text_instance().pk
            request.POST = post_data
        return super(BlogEntryAdmin, self).add_plugin(request)

    def edit_plugin(self, request, plugin_id):
        plugin = get_object_or_404(CMSPlugin, pk=plugin_id)
        entry = BlogEntry.objects.get(content=plugin.placeholder)
        setattr(request, 'current_page', entry.get_layout().from_page)
        return super(BlogEntryAdmin, self).edit_plugin(request, plugin_id)

    def get_fieldsets(self, request, obj=None):
        if obj and obj.pk:
            self.fieldsets = self.change_form_fieldsets
        else:
            self.fieldsets = ()
        return super(BlogEntryAdmin, self).get_fieldsets(request, obj)


admin.site.register(Blog, BlogAdmin)
admin.site.register(BlogEntry, BlogEntryAdmin)
