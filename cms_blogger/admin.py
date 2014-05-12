from django.conf.urls.defaults import patterns, url
from django.contrib import admin
from django.contrib.sites.models import Site
from django.contrib.contenttypes.generic import GenericTabularInline
from django.core.exceptions import PermissionDenied
from django.core.files.images import get_image_dimensions
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from django.utils.html import escapejs
from django.utils import timezone
from django.utils.translation import get_language, ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt

from cms.admin.placeholderadmin import PlaceholderAdmin
from cms.models import Title, CMSPlugin
from menus.menu_pool import menu_pool
from menus.templatetags.menu_tags import cut_levels

from filer.utils.files import handle_upload, UploadException

from cms_layouts.models import Layout
from cms_layouts.slot_finder import get_mock_placeholder

from .changelists import BlogChangeList, BlogEntryChangeList
from .models import Blog, BlogEntryPage, BlogNavigationNode
from .forms import (
    BlogLayoutForm, BlogForm, BlogAddForm, BlogEntryPageAddForm,
    BlogEntryPageChangeForm, BlogLayoutInlineFormSet,
    EntryChangelistForm)
from .admin_helper import AdminHelper
from .settings import (ALLOWED_THUMBNAIL_IMAGE_TYPES,
                       MINIMUM_POSTER_IMAGE_WIDTH,
                       POSTER_IMAGE_ASPECT_RATIO,
                       POSTER_IMAGE_ASPECT_RATIO_ERROR)
from .widgets import ToggleWidget

import imghdr
import json
import os


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
                language=get_language()).values_list(
                    'page', 'page__level', 'title').order_by(
                        'page__tree_id', 'page__lft')
            available_choices = [
                (page, mark_safe('%s%s' % ('&nbsp;' * level * 2, title)))
                for page, level, title in available_choices]
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


class BlogAdmin(AdminHelper):
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
    )
    change_form_fieldsets = (
        ('Blog setup', {
            'fields': ['site', 'title', 'slug', 'tagline', 'branding_image',
                       'entries_slugs_with_date', 'categories'],
            'classes': ('extrapretty', ),
            'description': _('Blog Setup Description')
        }),
        ('Blog Users', {
            'fields': ['allowed_users', ],
            'classes': ('extrapretty', ),
            'description': _('Blog Allowed Users')
        }),
        ('Navigation', {
            'fields': [('in_navigation', 'location_in_navigation'), ],
            'classes': ('extrapretty',),
        }),
        ('Social media and commenting integration', {
            'fields': ['enable_facebook', 'enable_twitter',
                       'email_account_link'],
            'classes': ('collapse', 'extrapretty', )
        }),
        ('Disqus commenting integration', {
            'fields': ['enable_disqus', 'disqus_shortname',
                       'disable_disqus_for_mobile'],
            'classes': ('wide', 'extrapretty', 'collapse'),
            'description': _('Blog Disqus commenting Description')
        }),
    )
    prepopulated_fields = {"slug": ("title",)}

    def _get_nodes(self, request, nodes, node_id, output):
        for node in nodes:
            if node.id == node_id:
                output.append('<li class="current-node">')
            else:
                output.append('<li>')
            output.append(node.get_menu_title())
            if node.children:
                output.append('<span class="arrow-down"></span>')
                output.append('<ul>')
                self._get_nodes(request, node.children, node_id, output)
                output.append('</ul>')
            output.append('</li>')

    def _navigation_preview(self, request, nav_node):
        if not request or not nav_node:
            return '(Choose position)'
        nodes = menu_pool.get_nodes(request, None, None)
        nodes = cut_levels(nodes, 0, 1, 1, 100)
        nodes = menu_pool.apply_modifiers(
            nodes, request, None, None, post_cut=True)
        output = []
        node_id = nav_node.id * -1
        self._get_nodes(request, nodes, node_id, output)
        html_preview = ''.join(output)
        if 'current-node' not in html_preview:
            return "(Choose Position)"
        return html_preview

    def location_in_navigation(self, obj):
        if obj.id:
            nav_node = obj.navigation_node
            request = getattr(obj, '_request_for_navigation_preview', None)
            url = reverse('admin:cms_blogger-navigation-tool', args=[obj.id])
            output = []
            output.append(
                u'<a href="%s" class="add-another" id="add_id_navigation_node"'
                ' onclick="return showNavigationPopup(this);"> ' % url)
            output.append(
                u'<input type="button" value="Open Navigation Tool" /></a>')
            preview = self._navigation_preview(
                request, nav_node)
            output.append('<ul id="id_navigation_node_pretty">')
            output.append(preview)
            output.append('</ul')
            html_out = u''.join(output)
            html_out = mark_safe(html_out)
            return html_out
        else:
            return "(save first)"
    location_in_navigation.allow_tags = True
    location_in_navigation.short_description = 'Select location'

    def get_formsets(self, request, obj=None):
        # don't show layout inline in add view
        if obj and obj.pk:
            # set request for navigation_preview
            obj._request_for_navigation_preview = request
            return super(BlogAdmin, self).get_formsets(request, obj)
        return []

    def get_urls(self):
        urls = super(BlogAdmin, self).get_urls()
        url_patterns = patterns('',
            url(r'^(?P<blog_id>\d+)/navigation_tool/$',
                self.admin_site.admin_view(self.navigation_tool),
                name='cms_blogger-navigation-tool'),

            url(r'^(?P<blog_entry_id>\d+)/upload_file/$',
                self.admin_site.admin_view(self.upload_thumbnail),
                name='cms_blogger-upload-thumbnail'),

            url(r'^(?P<blog_entry_id>\d+)/delete_file/$',
                self.admin_site.admin_view(self.delete_thumbnail),
                name='cms_blogger-delete-thumbnail'),
        )
        url_patterns.extend(urls)
        return url_patterns

    @csrf_exempt
    def upload_thumbnail(self, request, blog_entry_id=None):

        try:
            blog_entry = BlogEntryPage.objects.get(id=blog_entry_id)

            if blog_entry.poster_image.name:
                blog_entry._old_poster_image = blog_entry.poster_image.name

        except BlogEntryPage.DoesNotExist:
            raise UploadException(
                "Blog entry with id={0} does not exist".format(id))

        mimetype = "application/json" if request.is_ajax() else "text/html"
        upload = None
        try:
            upload, filename, _ = handle_upload(request)
            validate_image_dimensions(upload)
            validate_image_size(upload, request)
            guessed_extension = imghdr.what(upload) or ""
            if guessed_extension not in ALLOWED_THUMBNAIL_IMAGE_TYPES:
                if not guessed_extension:
                    displayed_extension = "Unknown"
                else:
                    displayed_extension = guessed_extension
                raise UploadException(
                    displayed_extension + " file type not allowed."
                    " Please upload one of the following file types: " +
                    ", ".join(ALLOWED_THUMBNAIL_IMAGE_TYPES))

            extension = os.path.splitext(filename)[1]
            if not extension:
                # try to guess if it's an image and append extension

                if guessed_extension:
                    filename = '%s.%s' % (filename, guessed_extension)
            blog_entry.poster_image.save(filename, upload)
            json_response = {
                'label': unicode(blog_entry.poster_image.name),
                'url': blog_entry.poster_image.url,
            }
            return HttpResponse(
                json.dumps(json_response), mimetype=mimetype)
        except UploadException, e:
            return HttpResponse(
                json.dumps({'error': unicode(e)}), mimetype=mimetype)
        finally:
            if upload:
                upload.close() #memory leak if not closed?

    @csrf_exempt
    def delete_thumbnail(self, request, blog_entry_id=None):
        try:
            blog_entry = BlogEntryPage.objects.get(id=blog_entry_id)
        except BlogEntryPage.DoesNotExist:
            return HttpResponseNotFound("BlogEntry does not exist")
        if blog_entry.poster_image and blog_entry.poster_image.name:
            blog_entry.poster_image.delete()
            return HttpResponse("OK")
        return HttpResponseNotFound("No file to delete")

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
                nav_node = BlogNavigationNode.objects.create(**data)
                nav_node.blog_set.add(blog)
            else:
                for attname, value in data.items():
                    setattr(nav_node, attname, value)
                nav_node.save()

            preview = self._navigation_preview(request, nav_node)
            return HttpResponse(
                '<!DOCTYPE html><html><head><title></title></head><body>'
                '<script type="text/javascript">opener.closeNavigationPopup'
                '(window, "%s");</script></body></html>' % \
                    (escapejs(preview)), )
        context = RequestContext(request)
        context.update({
            'title': 'Edit navigation menu',
            'is_popup': "_popup" in request.REQUEST
        })

        if blog.navigation_node:
            context.update({'initial_blog_node': blog.navigation_node, })
        return render_to_response(
            'admin/cms_blogger/blog/navigation.html', context)


def validate_image_dimensions(upload):
    width, height = get_image_dimensions(upload)
    if width < MINIMUM_POSTER_IMAGE_WIDTH:
        raise UploadException(
            "Image width should be larger than {0}px".format(
                MINIMUM_POSTER_IMAGE_WIDTH))

    delta_ratio = width / float(height) - POSTER_IMAGE_ASPECT_RATIO
    if abs(delta_ratio) > POSTER_IMAGE_ASPECT_RATIO_ERROR:
        horizontal_text, vertical_text = "narrower", "taller"
        if delta_ratio < 0:
            horizontal_text, vertical_text = "wider", "shorter"

        horizontal_px, vertical_px = map(
            lambda x: abs(int(round(x))), [
                height * POSTER_IMAGE_ASPECT_RATIO - width,
                width / POSTER_IMAGE_ASPECT_RATIO - height])

        raise UploadException(
            "Image doesn't have a 16:9 aspect ratio. "
            "It should be {0}px {1} or {2}px {3}".format(
                horizontal_px, horizontal_text,
                vertical_px, vertical_text))

def validate_image_size(upload, request):
    if ('CONTENT_LENGTH' in request.META and
        len(upload) != int(request.META.get('CONTENT_LENGTH'))):

        raise UploadException(
            "File not uploaded completely. "
            "Only {0} bytes uploaded".format(len(upload)))



class BlogEntryPageAdmin(AdminHelper, PlaceholderAdmin):
    list_editable = ('is_published', )
    custom_changelist_class = BlogEntryChangeList
    list_display = ('__str__', 'slug', 'blog', 'is_published',
                    'entry_authors')
    search_fields = ('title', 'blog__title')

    # move_entries is enabled by default, removed if user.is_superuser
    # really bad design/security issue
    actions = ['make_published', 'make_unpublished', 'move_entries']

    add_form_template = 'admin/cms_blogger/blogentrypage/add_form.html'
    add_form = BlogEntryPageAddForm
    change_form = BlogEntryPageChangeForm
    formfield_overrides = {
        models.BooleanField: {'widget': ToggleWidget}
    }
    change_form_fieldsets = (
        (None, {
            'fields': ['title', 'authors', 'short_description', ],
        }),

        (None, {
            'fields': ['poster_image_uploader', ],
            'classes': ('poster-image',)
        }),

        ("Credit/Caption", {
            'fields': ['caption', 'credit'],
            'classes': ('collapsible-inner', 'closed')

        }),

        (None, {
            'fields': ['preview_on_top', 'body', 'preview_on_bottom'],
            'classes': ('no-border', 'body-wrapper')
        }),
        (None, {
            'fields': ['publish', 'save_button'],
            'classes': ('right-col', )
        }),
        ('Schedule Publish', {
            'fields': ['start_publication', 'schedule_publish'],
            'description': _('Schedule Start Date description'),
            'classes': ('right-col', 'collapsible-inner', 'hide-label',
                        'closed')
        }),
        ('Schedule Unpublish', {
            'fields': ['end_publication', 'schedule_unpublish'],
            'description': _('Schedule End Date description'),
            'classes': ('right-col', 'collapsible-inner', 'hide-label',
                        'closed')
        }),
        (None, {
            'fields': ['categories', ],
            'classes': ('right-col', )
        }),
        ('Advanced Options', {
            'fields': ['seo_title', 'meta_keywords', 'disqus_enabled'],
            'classes': ('right-col', 'collapse')
        }),

    )

    def get_urls(self):
        urls = super(BlogEntryPageAdmin, self).get_urls()
        url_patterns = patterns('',
            url(r'^(?P<entry_id>\d+)/preview/$',
                self.admin_site.admin_view(self.preview),
                name='cms_blogger-entry-preview'), )
        url_patterns.extend(urls)
        return url_patterns

    def preview(self, request, entry_id):
        entry = get_object_or_404(self.model, id=entry_id)
        if 'body' in request.POST:
            entry.content = get_mock_placeholder(
                get_language(), request.POST.get('body') or 'Sample Content')
        return entry.render_to_response(request)

    def get_changelist_form(self, request, **kwargs):
        return EntryChangelistForm

    def change_view(self, request, object_id, form_url='', extra_context=None):
        response = super(BlogEntryPageAdmin, self).change_view(
            request, object_id, form_url, extra_context)
        if hasattr(response, 'context_data'):
            context = response.context_data
            context['media'] = self._upgrade_jquery(context['media'])
        return response

    def queryset(self, request):
        qs = super(BlogEntryPageAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(blog__allowed_users=request.user)

    def lookup_allowed(self, lookup, value):
        if lookup == BlogEntryChangeList.site_lookup:
            return True
        return super(BlogEntryPageAdmin, self).lookup_allowed(lookup, value)

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

    def make_published(self, request, queryset):
        # cannot publish draft entries
        draft_entries = Q(Q(title__isnull=True) | Q(title__exact='') |
                          Q(short_description__isnull=True) |
                          Q(short_description__exact='') |
                          Q(blog__isnull=True))
        queryset.exclude(draft_entries).filter(is_published=False).update(
            is_published=True, publication_date=timezone.now())
    make_published.short_description = "Publish entries"

    def move_entries(self, request, queryset):
        import ipdb; ipdb.set_trace()
        if request.method == "POST" and request.POST.get('post'):
            print "ko"
        return render_to_response(
            'admin/cms_blogger/blog/move_entries.html', {
                    "blogentries": queryset, 
                    "blogs": Blog.objects.filter(~Q(id=queryset[0].blog.id)), #might not be ideal
                }, context_instance = RequestContext(request))

    move_entries.short_description = "Move entries to another blog"

    def make_unpublished(self, request, queryset):
        queryset.filter(is_published=True).update(
            is_published=False, publication_date=timezone.now())
    make_unpublished.short_description = "Unpublish entries"

    def entry_authors(self, entry):
        return entry.authors_display_name
    entry_authors.allow_tags = True

    def get_actions(self, request):
        actions = super(BlogEntryPageAdmin, self).get_actions(request) 
        if not request.user.is_superuser:
            del actions['move_entries']
        return actions

admin.site.register(Blog, BlogAdmin)
admin.site.register(BlogEntryPage, BlogEntryPageAdmin)
