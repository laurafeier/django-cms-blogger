from django.contrib import admin
from django.contrib.sites.models import Site
from django.contrib.contenttypes.generic import GenericTabularInline
from django.contrib.admin.templatetags.admin_static import static
from django.db import models
from django.forms import HiddenInput, Media
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
from menus.menu_pool import menu_pool
from menus.templatetags.menu_tags import cut_levels

from cms_layouts.models import Layout
from .models import Blog, BlogEntryPage, BlogNavigationNode
from .forms import (
    BlogLayoutForm, BlogForm, BlogAddForm, BlogEntryPageAddForm,
    BlogEntryPageChangeForm, BlogLayoutInlineFormSet)
from .changelists import BlogChangeList, BlogEntryChangeList
from .widgets import ToggleWidget
from filer.utils.files import handle_upload, UploadException
import imghdr
from django.views.decorators.csrf import csrf_exempt
from os import path as os_path
from django.utils import simplejson


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
                    'page', 'page__level', 'title')
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
        ('Blog Users', {
            'fields': ['allowed_users', ],
            'classes': ('extrapretty', ),
            'description': _('Blog Allowed Users')
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
                self.admin_site.admin_view(self.upload_thumbnail), #what is this
                name='cms_blogger-upload-thumbnail'),

            url(r'^(?P<blog_entry_id>\d+)/delete_file/$',
                self.admin_site.admin_view(self.delete_thumbnail), #what is this
                name='cms_blogger-delete-thumbnail'),
        )
        url_patterns.extend(urls)
        return url_patterns

    @csrf_exempt
    def upload_thumbnail(self, request, blog_entry_id=None):
        try:
            print "before "*20
            blog_entry = BlogEntryPage.objects.get(id=blog_entry_id)

            # if this blog is in BlogEntryPage.__init__ it will be called when
            # saving a blog and the current file gets deleted 
            if blog_entry.thumbnail_image.name:
                blog_entry._old_thumbnail = (
                    blog_entry.thumbnail_image.storage, 
                    blog_entry.thumbnail_image.name)

            print "after "*20
        except BlogEntryPage.DoesNotExist:
            blog_entry = None
        if blog_entry is not None:
            mimetype = "application/json" if request.is_ajax() else "text/html"
            upload = None
            try:
                upload, filename, _ = handle_upload(request)

                extension = os_path.splitext(filename)[1]
                if not extension:
                    # try to guess if it's an image and append extension
                    # imghdr will detect file is a '.jpeg', '.png' or '.gif' image
                    guessed_extension = imghdr.what(upload)
                    if guessed_extension:
                        filename = '%s.%s' % (filename, guessed_extension)
                blog_entry.thumbnail_image.save(filename, upload)
                json_response = {
                    'label': unicode(blog_entry.thumbnail_image.name),
                    'url': blog_entry.thumbnail_image.url,
                }
                return HttpResponse(simplejson.dumps(json_response),
                                        mimetype=mimetype)
            except UploadException, e:
                return HttpResponse(simplejson.dumps({'error': unicode(e)}),
                                    mimetype=mimetype)
            finally:
                if upload:
                    upload.close()

    @csrf_exempt
    def delete_thumbnail(self, request, blog_entry_id=None):
        try:
            blog_entry = BlogEntryPage.objects.get(id=blog_entry_id)
        except BlogEntryPage.DoesNotExist:
            blog_entry = None
        if blog_entry:
            if blog_entry.thumbnail_image and blog_entry.thumbnail_image.name:
                blog_entry.thumbnail_image.delete()
                #thumbnail = blog_entry.thumbnail_image
                #thumbnail.storage.delete(thumbnail.name)
                #blog_entry.thumbnail.name = ""
                #blog_entry.save() 
                return HttpResponse("OK")
            return HttpResponse("No file to delete")
        return HttpResponse("BlogEntry does not exist") 
     
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
            'current_site': Site.objects.get_current(),
            'title': 'Edit navigation menu',
            'is_popup': "_popup" in request.REQUEST
        })

        if blog.navigation_node:
            context.update({'initial_blog_node': blog.navigation_node,})
        return render_to_response(
            'admin/cms_blogger/blog/navigation.html', context)


class BlogEntryPageAdmin(CustomAdmin, PlaceholderAdmin):
    custom_changelist_class = BlogEntryChangeList
    list_display = ('__str__', 'slug', 'blog')
    search_fields = ('title', 'blog__title')
    add_form_template = 'admin/cms_blogger/blogentrypage/add_form.html'
    add_form = BlogEntryPageAddForm
    change_form = BlogEntryPageChangeForm
    readonly_in_change_form = ['blog', ]
    change_form_fieldsets = (
        (None, {
            'fields': [
                'title', 'blog', ('slug', 'publication_date'),
                'upload_button',
                'categories',
                'author', 'abstract', 'body',
                ('is_published', 'start_publication', 'end_publication'),
                'meta_description', 'meta_keywords'],
        }),)

    @property
    def media(self):
        # upgrade jquery and cms jquery UI
        super_media = super(BlogEntryPageAdmin, self).media
        new_media = Media()
        new_media.add_css(super_media._css)

        new_jquery_version = static('cms_blogger/js/jquery-1.9.1.min.js')
        new_jquery_ui_version = static('cms_blogger/js/jquery-ui.min.js')
        # make sure all jquery namespaces point to the same jquery
        jquery_namspace = static('cms_blogger/js/jQuery-patch.js')
        django_jquery_urls = [static('admin/js/jquery.js'),
                              static('admin/js/jquery.min.js')]

        for js in super_media._js:
            if js in django_jquery_urls:
                new_media.add_js((new_jquery_version, ))
            elif js == static('admin/js/jquery.init.js'):
                new_media.add_js((js, jquery_namspace))
            elif js.startswith(static('cms/js/libs/jquery.ui.')):
                new_media.add_js((new_jquery_ui_version, ))
            else:
                new_media.add_js((js, ))

        return new_media

    def get_form(self, request, obj=None, **kwargs):
        formCls = super(BlogEntryPageAdmin, self).get_form(
            request, obj, **kwargs)
        # set initial
        if obj and not obj.author:
            obj.author = request.user
        if not obj:
            # filter available blog choices
            site = Site.objects.get_current()
            blog_field = formCls.base_fields['blog']
            allowed_blogs = blog_field.queryset.filter(site=site)
            if not request.user.is_superuser:
                allowed_blogs = allowed_blogs.filter(
                    allowed_users=request.user)
            blog_field.queryset = allowed_blogs
            blog_field.widget.can_add_related = False
        return formCls

    def queryset(self, request):
        qs = super(BlogEntryPageAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(blog__allowed_users=request.user)

    def save_related(self, request, form, formsets, change):
        super(BlogEntryPageAdmin, self).save_related(
            request, form, formsets, change)
        submitted_categories = form.cleaned_data.get('categories', [])
        entry = form.instance
        if not entry.blog:
            entry.categories = []
        else:
            ids_in_blog = entry.blog.categories.values_list('pk', flat=True)
            entry.categories = [
                valid_category
                for valid_category in submitted_categories
                if valid_category.pk in ids_in_blog]

    def lookup_allowed(self, lookup, value):
        if lookup == BlogEntryChangeList.site_lookup:
            return True
        return super(BlogEntryPageAdmin, self).lookup_allowed(lookup, value)

    def get_prepopulated_fields(self, request, obj=None):
        if obj and obj.pk:
            self.prepopulated_fields = {"slug": ("title",)}
        else:
            self.prepopulated_fields = {}
        return super(BlogEntryPageAdmin, self).get_prepopulated_fields(request, obj)

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
