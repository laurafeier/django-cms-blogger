from django.contrib import admin
from django.contrib.sites.models import Site
from django.contrib.contenttypes.generic import GenericTabularInline
from django.db import models
from django.forms import HiddenInput
from django.utils.html import escapejs
from django.utils.translation import get_language, ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.conf.urls.defaults import patterns, url
from django.conf import settings
from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from django.http import HttpResponse

from cms.admin.placeholderadmin import PlaceholderAdmin
from cms.models import Title, CMSPlugin

from cms_layouts.models import Layout
from .models import Blog, BlogEntryPage, BlogNavigationNode
from .forms import (
    BlogLayoutForm, BlogForm, BlogAddForm, BlogEntryPageAddForm,
    BlogEntryPageChangeForm, BlogLayoutInlineFormSet)
from .blog_changelist import BlogChangeList
from .widgets import ToggleWidget


class BlogLayoutInline(GenericTabularInline):
    form = BlogLayoutForm
    readonly_fields = ('layout_customization', )
    model = Layout
    extra = 0
    max_num = len(Blog.LAYOUTS_CHOICES.items())
    formset = BlogLayoutInlineFormSet
    description = _("Blog Layouts description")
    verbose_name = _("Blog Layouts Chooser")
    verbose_name_plural = _("Blog Layouts Chooser")

    def get_formset(self, request, obj=None, **kwargs):
        formSet = super(BlogLayoutInline, self).get_formset(
            request, obj, **kwargs)
        # show one form if there are no layouts
        if obj and obj.layouts.count() == 0:
            formSet.extra = 1
        else:
            formSet.extra = 0

        if obj:
            available_choices = Title.objects.filter(
                page__site=obj.site,
                language=get_language()).values_list('page', 'title')
        else:
            available_choices = Title.objects.get_empty_query_set()
        page_field = formSet.form.base_fields['from_page']
        page_field.widget.choices = available_choices
        return formSet

    def layout_customization(self, obj):
        if obj.id:
            pattern = 'admin:%s_%s_change' % (obj._meta.app_label,
                                              obj._meta.module_name)
            url = reverse(pattern,  args=[obj.id])
            url_tag = ("<a href='%s'>Customize Layout "
                       "content</a>" % url)
            return url_tag
        else:
            return "(save to customize layout)"
    layout_customization.allow_tags = True


class CustomAdmin(admin.ModelAdmin):

    def get_changelist(self, request, **kwargs):
        if hasattr(self, 'custom_changelist_class'):
            return self.custom_changelist_class
        return super(CustomAdmin, self).get_changelist(request, **kwargs)

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
            self.form = self.add_form
            # reset declared_fieldsets
            self.fieldsets = getattr(self, 'add_form_fieldsets', ())
        elif obj and hasattr(self, 'change_form'):
            self.form = self.change_form
            # reset declared_fieldsets
            self.fieldsets = getattr(self, 'change_form_fieldsets', ())
        return super(CustomAdmin, self).get_form(request, obj, **kwargs)


class BlogAdmin(CustomAdmin):
    custom_changelist_class = BlogChangeList
    inlines = [BlogLayoutInline, ]
    add_form = BlogAddForm
    change_form = BlogForm
    search_fields = ['title', 'site__name']
    list_display = ('title', 'slug', 'site')
    readonly_in_change_form = ['site', 'location_in_navigation']
    formfield_overrides = {
        models.BooleanField: {'widget': ToggleWidget}
    }
    add_form_fieldsets = (
        (None, {
            'fields': ['title', 'slug'],
            'classes': ('general',)
            }),
        ('Hidden', {
            'fields': ('site',),
            'classes': ('hide-me',),
            })
    )
    change_form_fieldsets = (
        ('Blog setup', {
            'fields': ['site', 'title', 'slug', 'tagline', 'branding_image',
                       'entries_slugs_with_date', 'categories'],
            'classes': ('extrapretty', ),
            'description': _('Blog Setup Description')
        }),
        ('Navigation', {
            'fields': [('in_navigation', 'location_in_navigation'), ],
            'classes': ('extrapretty',),
        }),
        ('Social media and commentig integration', {
            'fields': ['enable_facebook', 'enable_twitter',
                       'email_account_link'],
            'classes': ('collapse', 'extrapretty', )
        }),
        ('Disqus commentig integration', {
            'fields': ['enable_disqus', 'disqus_shortname',
                       'disable_disqus_for_mobile'],
            'classes': ('wide', 'extrapretty', 'collapse'),
            'description': _('Blog Disqus commentig Description')
        }),
    )
    prepopulated_fields = {"slug": ("title",)}

    def get_form(self, request, obj=None, **kwargs):
        formCls = super(BlogAdmin, self).get_form(request, obj, **kwargs)

        if not obj and 'site' in formCls.base_fields:
            site_field = formCls.base_fields['site']
            site_field.choices = []
            site_field.widget = HiddenInput()
            site_field.initial = Site.objects.get_current().pk

        return formCls

    def location_in_navigation(self, obj):
        if obj.id:
            url = reverse('admin:cms_blogger-navigation-tool', args=[obj.id])
            name = 'navigation_node'
            output = []
            output.append(
                u'<a href="%s" class="add-another" id="add_id_%s" '
                'onclick="return showNavigationPopup(this);"> ' % (
                    url, name))
            output.append(
                u'<button>Open Navigation Tool</button></a>')
            output.append(
                u'<span id="id_%s_pretty">%s</span>' % (
                    name, obj.navigation_node if obj.navigation_node else ''))

            return mark_safe(u''.join(output))
        else:
            return "(save first)"
    location_in_navigation.allow_tags = True
    location_in_navigation.short_description = 'Select location'

    def save_related(self, request, form, formsets, change):
        super(BlogAdmin, self).save_related(request, form, formsets, change)
        submitted_categories = form.cleaned_data.get('categories', [])

        for existing in form.instance.categories.all():
            if existing not in submitted_categories:
                existing.delete()
        form.instance.categories = submitted_categories

    def get_formsets(self, request, obj=None):
        # don't show layout inline in add view
        if obj and obj.pk:
            return super(BlogAdmin, self).get_formsets(request, obj)
        return []

    def get_urls(self):
        urls = super(BlogAdmin, self).get_urls()
        url_patterns = patterns('',
            url(r'^(?P<blog_id>\d+)/navigation_tool/$',
                self.admin_site.admin_view(self.navigation_tool),
                name='cms_blogger-navigation-tool'), )
        url_patterns.extend(urls)
        return url_patterns

    def navigation_tool(self, request, blog_id):
        if (request.method not in ['GET', 'POST'] or
                not "_popup" in request.REQUEST):
            raise PermissionDenied

        blog = get_object_or_404(Blog, id=blog_id)

        if request.method == 'POST':
            data = {
                'parent_node_id': request.POST.get('parent_node_id') or None,
                'text': request.POST.get('text') or blog.title[:15],
                'position': int(request.POST.get('position'))
            }
            nav_node = blog.navigation_node
            if not nav_node:
                new_node = BlogNavigationNode.objects.create(**data)
                new_node.blog_set.add(blog)
            else:
                for attname, value in data.items():
                    setattr(nav_node, attname, value)
                nav_node.save()
            return HttpResponse(
                '<!DOCTYPE html><html><head><title></title></head><body>'
                '<script type="text/javascript">opener.closeNavigationPopup'
                '(window, "%s");</script></body></html>' % \
                    (escapejs(nav_node)), )
        context = RequestContext(request)
        context.update({
            'current_site': Site.objects.get_current(),
            'title': 'Edit navigation menu',
            'is_popup': "_popup" in request.REQUEST
        })

        if blog.navigation_node:
            context.update({'initial_blog_node': blog.navigation_node,})
        return render_to_response(
            'admin/cms_blogger/blog/navigation.html', context)


class BlogEntryPageAdmin(CustomAdmin, PlaceholderAdmin):
    list_display = ('__str__', 'slug', 'blog')
    search_fields = ('title', 'blog__title')
    add_form_template = 'admin/cms_blogger/blogentrypage/add_form.html'
    add_form = BlogEntryPageAddForm
    change_form = BlogEntryPageChangeForm
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
        if 'parent_id' in request.POST:
            entry = get_object_or_404(
                BlogEntryPage, pk=request.POST['parent_id'])
            post_data = request.POST.copy()
            post_data['parent_id'] = entry.get_content_plugin().pk
            request.POST = post_data
        return super(BlogEntryPageAdmin, self).add_plugin(request)

    def edit_plugin(self, request, plugin_id):
        plugin = get_object_or_404(CMSPlugin, pk=plugin_id)
        entry = BlogEntryPage.objects.get(content=plugin.placeholder)
        setattr(request, 'current_page', entry.get_layout().from_page)
        return super(BlogEntryPageAdmin, self).edit_plugin(request, plugin_id)


admin.site.register(Blog, BlogAdmin)
admin.site.register(BlogEntryPage, BlogEntryPageAdmin)
