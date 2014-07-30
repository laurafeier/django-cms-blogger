from django.conf.urls.defaults import patterns, url
from django.contrib import admin, messages
from django.contrib.admin.templatetags.admin_static import static
from django.contrib.contenttypes.generic import GenericTabularInline
from django.core.exceptions import PermissionDenied
from django.core.files.images import get_image_dimensions
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template.context import RequestContext
from django.utils.html import escape
from django.utils import timezone
from django.utils.translation import get_language, ugettext_lazy as _
from django.utils.translation import ungettext
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from cms.admin.placeholderadmin import PlaceholderAdmin
from cms.models import Title, CMSPlugin
from menus.menu_pool import menu_pool
from menus.templatetags.menu_tags import cut_levels

from filer.utils.files import handle_upload, UploadException

from cms_layouts.models import Layout
from cms_layouts.slot_finder import get_mock_placeholder

from cms_blogger import forms, changelists
from .models import (
    Blog, BlogCategory, BlogEntryPage, BlogNavigationNode, HomeBlog)
from .admin_helper import AdminHelper, WizardForm
from .settings import ALLOWED_THUMBNAIL_IMAGE_TYPES
from .widgets import ToggleWidget
from .utils import resize_image, get_allowed_sites, get_current_site
import imghdr
import json
import os
import urllib


class AbstractBlogLayoutInline(GenericTabularInline):
    readonly_fields = ('layout_customization', )
    model = Layout
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        formSet = super(AbstractBlogLayoutInline, self).get_formset(
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
            url_tag = ("<a href='%s' id='add_layout_id_%s' "
                       "onclick='return showAddAnotherPopup(this);'>"
                       "<input type='button' value='Customize Layout' />"
                       "</a>" % (url, obj.id))

            return url_tag
        else:
            return "(save to customize layout)"
    layout_customization.allow_tags = True


class BlogLayoutInline(AbstractBlogLayoutInline):
    form = forms.BlogLayoutForm
    formset = forms.BlogLayoutInlineFormSet
    max_num = len(Blog.LAYOUTS_CHOICES.items())
    description = _("Blog Layouts description")
    verbose_name = _("Blog Layouts Chooser")
    verbose_name_plural = _("Blog Layouts Chooser")


class HomeBlogLayoutInline(AbstractBlogLayoutInline):
    form = forms.LayoutForm
    formset = forms.HomeBlogLayoutInlineFormSet
    max_num = 1
    description = _("Super Landing Page Layout description")
    verbose_name = _("Super Landing Page Layout Chooser")
    verbose_name_plural = _("Super Landing Page Layout Chooser")


class AbstractBlogAdmin(AdminHelper):
    formfield_overrides = {
        models.BooleanField: {'widget': ToggleWidget}
    }
    class Media:
        css = {
            'all': (static('cms_blogger/css/redmond-jquery-ui.css'), )}
        js = (static('cms_blogger/js/jquery-1.9.1.min.js'),
              static("cms_blogger/js/jquery-ui.min.js"), )

    #### NAVIGATION ####
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
            return ''
        nodes = menu_pool.get_nodes(request, None, None)
        nodes = cut_levels(nodes, 0, 1, 1, 100)
        nodes = menu_pool.apply_modifiers(
            nodes, request, None, None, post_cut=True)
        output = []
        self._get_nodes(request, nodes, nav_node.menu_id, output)
        html_preview = ''.join(output)
        if 'current-node' not in html_preview:
            return ""
        return html_preview

    def location_in_navigation(self, obj):
        if obj.id:
            nav_node = obj.navigation_node
            request = getattr(obj, '_request_for_navigation_preview', None)
            info = self.model._meta.app_label, self.model._meta.module_name
            url = reverse('admin:cms_blogger-%s-%s-navigation-tool' % info,
                          args=[obj.id])
            output = []
            output.append(
                u'<a href="%s" class="add-another" id="add_id_navigation_node"'
                ' onclick="return showNavigationPopup(this);"> ' % url)
            output.append(
                u'<input type="button" value="Open Navigation Tool" /></a>')
            preview = self._navigation_preview(request, nav_node)
            hide = 'style="display:none"'
            if preview:
                hide = ''
            output.append('<ul id="id_navigation_node_pretty" %s>' % hide)
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
        if self.form in (forms.BlogForm, forms.HomeBlogForm):
            # set request for navigation_preview
            obj._request_for_navigation_preview = request
            return super(AbstractBlogAdmin, self).get_formsets(request, obj)
        return []

    def navigation_tool(self, request, blog_id):
        if (request.method not in ['GET', 'POST'] or
                not "_popup" in request.REQUEST):
            raise PermissionDenied

        blog = get_object_or_404(self.model, id=blog_id)

        if request.method == 'POST':
            data = {
                'parent_node_id': request.POST.get('parent_node_id') or None,
                'text': (request.POST.get('text') or blog.title)[:15],
                'position': int(request.POST.get('position'))
            }
            nav_node = blog.navigation_node
            if not nav_node:
                nav_node = BlogNavigationNode.objects.create(**data)
                blog.navigation_node = nav_node
                blog.save()
            else:
                for attname, value in data.items():
                    setattr(nav_node, attname, value)
                nav_node.save()

            preview = self._navigation_preview(request, nav_node)
            return HttpResponse(
                '<!DOCTYPE html><html><head><title></title></head><body>'
                '<script type="text/javascript">opener.closeNavigationPopup'
                '(window, "%s");</script></body></html>' % (
                    escape(preview)), )
        context = RequestContext(request)
        context.update({
            'title': 'Edit navigation menu',
            'is_popup': "_popup" in request.REQUEST
        })
        if blog.navigation_node:
            context.update({'initial_blog_node': blog.navigation_node, })
        return render_to_response(
            'admin/cms_blogger/blog/navigation.html', context)

    def get_urls(self):
        urls = super(AbstractBlogAdmin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.module_name
        url_patterns = patterns(
            '',
            url(r'^(?P<blog_id>\d+)/navigation_tool/$',
                self.admin_site.admin_view(self.navigation_tool),
                name='cms_blogger-%s-%s-navigation-tool' % info), )
        url_patterns.extend(urls)
        return url_patterns

    ### PERMISSIONS ###
    def get_current_site(self, request):
        return get_current_site(request, self.model)

    def _is_allowed(self, request, obj=None):
        if request.user.is_superuser:
            return True
        current_site = self.get_current_site(request)
        return current_site in get_allowed_sites(request, self.model)

    def has_add_permission(self, request):
        can_add = super(AbstractBlogAdmin, self).has_add_permission(request)
        return can_add and self._is_allowed(request)

    def has_change_permission(self, request, obj=None):
        can_change = super(AbstractBlogAdmin, self)\
            .has_change_permission(request, obj)
        return can_change and self._is_allowed(request, obj)

    def has_delete_permission(self, request, obj=None):
        can_delete = super(AbstractBlogAdmin, self)\
            .has_delete_permission(request, obj)
        return can_delete and self._is_allowed(request, obj)


class BlogAdmin(AbstractBlogAdmin):
    custom_changelist_class = changelists.BlogChangeList
    inlines = [BlogLayoutInline, ]
    wizard_forms = (
        WizardForm(form=forms.BlogAddForm,
                   fieldsets='add_form_fieldsets',
                   prepopulated='prepopulated_fields',
                   when=lambda obj: True if not obj else False,
                   show_next=True),
        WizardForm(form=forms.BlogLayoutMissingForm,
                   fieldsets=((None, {'fields': ['from_page', ]}), ),
                   when=lambda obj: obj and not obj.layouts.exists(),
                   show_next=True),
        WizardForm(form=forms.BlogForm,
                   fieldsets='change_form_fieldsets',
                   readonly='readonly_in_change_form',
                   prepopulated='prepopulated_fields',
                   when=lambda obj: True if obj else False))
    search_fields = ['title', 'site__name']
    list_display = ('title', 'slug', 'site')
    readonly_in_change_form = ['site', 'location_in_navigation']
    add_form_fieldsets = (
        (None, {
            'fields': ['title', 'slug'],
            'classes': ('general',)
        }),
    )
    change_form_fieldsets = (
        ('Blog setup', {
            'fields': ['site', 'title', 'slug', 'tagline', 'branding_image',
                       'categories'],
            'classes': ('extrapretty', ),
            'description': _('Blog Setup Description')
        }),
        ('Blog Users', {
            'fields': ['allowed_users', ],
            'classes': ('extrapretty', ),
            'description': _('Blog Allowed Users')
        }),
        ('Advanced Settings', {
            'fields': ['entries_slugs_with_date',
                       ('in_navigation', 'location_in_navigation'), ],
            'classes': ('extrapretty', 'collapse'),
        }),
        ('Social media integration', {
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


class HomeBlogAdmin(AbstractBlogAdmin):
    list_display = ('title', 'site', )
    search_fields = ['title', 'site__name']
    inlines = [HomeBlogLayoutInline, ]
    add_form = forms.HomeBlogAddForm
    change_form = forms.HomeBlogForm
    add_form_fieldsets = (
        (None, {'fields': ['site', 'title', ], 'classes': ('general', )}), )
    change_form_fieldsets = (
        (None, {
            'fields': ('site', 'title', 'tagline', 'branding_image'),
            'description': _('Home Blog Setup Description')
        }),
        ('Advanced Settings', {
            'classes': ('extrapretty', 'collapse'),
            'fields': (('in_navigation', 'location_in_navigation'), )
        }),
    )
    readonly_in_change_form = ['site', 'location_in_navigation']

    ### PERMISSIONS ###
    def queryset(self, request):
        qs = super(HomeBlogAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(site__in=get_allowed_sites(request, self.model))

    def _is_allowed(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return get_allowed_sites(request, self.model).exists()

    def has_add_permission(self, request):
        can_add = super(AbstractBlogAdmin, self).has_add_permission(request)
        sites_without_home_blog = get_allowed_sites(request, self.model)\
            .filter(homeblog__isnull=True).exists()
        return can_add and sites_without_home_blog


class CurrentSiteBlogFilter(admin.filters.RelatedFieldListFilter):

    def __init__(self, field, request, params, model, model_admin, field_path):
        super(CurrentSiteBlogFilter, self).__init__(
            field, request, params, model, model_admin, field_path)
        working_site = request.session['cms_admin_site']
        self.lookup_choices = Blog.objects.filter(
            site=working_site).values_list('pk', 'title')


class BlogEntryPageAdmin(AdminHelper, PlaceholderAdmin):
    list_editable = ('is_published', )
    custom_changelist_class = changelists.BlogEntryChangeList
    list_display = ('__str__', 'slug', 'blog', 'is_published', 'published_at',
                    'entry_authors', 'categories_assigned')
    list_filter = (('blog', CurrentSiteBlogFilter), )
    list_per_page = 50
    search_fields = ('title', 'blog__title')
    actions = ['make_published', 'make_unpublished', 'move_entries']
    add_form_template = 'admin/cms_blogger/blogentrypage/add_form.html'
    add_form = forms.BlogEntryPageAddForm
    change_form = forms.BlogEntryPageChangeForm
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
            'fields': ['seo_title', 'meta_keywords',
                       'disqus_enabled', 'enable_poster_image'],
            'classes': ('right-col', 'collapse')
        }),

    )

    class Media:
        js = ("cms_blogger/js/moment.min.js",)

    def get_changelist_form(self, request, **kwargs):
        return forms.EntryChangelistForm

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
        if lookup == BlogEntryPage.site_lookup:
            return True
        return super(BlogEntryPageAdmin, self).lookup_allowed(lookup, value)

    def get_actions(self, request):
        actions = super(BlogEntryPageAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions['move_entries']
        return actions

    def get_urls(self):
        urls = super(BlogEntryPageAdmin, self).get_urls()
        url_patterns = patterns(
            '',
            url(r'^(?P<blog_entry_id>\d+)/upload_file/$',
                self.admin_site.admin_view(self.upload_thumbnail),
                name='cms_blogger-upload-thumbnail'),

            url(r'^(?P<blog_entry_id>\d+)/delete_file/$',
                self.admin_site.admin_view(self.delete_thumbnail),
                name='cms_blogger-delete-thumbnail'),

            url(r'^move-entries/$',
                self.admin_site.admin_view(self.move_entries_view),
                name='cms_blogger-move-entries'),

            url(r'^(?P<entry_id>\d+)/preview/$',
                self.admin_site.admin_view(self.preview),
                name='cms_blogger-entry-preview'), )
        url_patterns.extend(urls)
        return url_patterns

    ### CUSTOM VIEWS ###
    def preview(self, request, entry_id):
        entry = get_object_or_404(self.model, id=entry_id)
        if 'body' in request.POST:
            entry.content = get_mock_placeholder(
                get_language(), request.POST.get('body') or 'Sample Content')
        return entry.render_to_response(request)

    @csrf_exempt
    def upload_thumbnail(self, request, blog_entry_id=None):
        try:
            blog_entry = BlogEntryPage.objects.get(id=blog_entry_id)
            # hold the initial file name in order to delete it after the
            #   uploaded file is saved. Deletion takes place in the model's
            #   save method
            blog_entry._old_poster_image = blog_entry.poster_image.name
        except BlogEntryPage.DoesNotExist:
            raise UploadException(
                "Blog entry with id %s does not exist" % blog_entry_id)

        mimetype = "application/json" if request.is_ajax() else "text/html"
        upload = None
        try:
            upload, full_filename, _ = handle_upload(request)
            filename, extension = os.path.splitext(
                os.path.basename(full_filename))
            # check if it's an image type we can handle
            extension = (imghdr.what(upload) or extension).lstrip('.')
            if extension not in ALLOWED_THUMBNAIL_IMAGE_TYPES:
                displayed_extension = extension or "Unknown"
                raise UploadException(
                    displayed_extension + " file type not allowed."
                    " Please upload one of the following file types: " +
                    ", ".join(ALLOWED_THUMBNAIL_IMAGE_TYPES))

            if not all(get_image_dimensions(upload)):
                raise UploadException(
                    "Image width and height should be greater than 0px")
            try:
                upload.name = ''.join((filename, os.path.extsep, extension))
                blog_entry.poster_image = resize_image(upload)
            except Exception, e:
                raise UploadException("Cannot resize image: %s" % e.message)
            # save new image
            blog_entry.save()
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
                upload.close()

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

    def move_entries_view(self, request):
        if not request.user.is_superuser:
            messages.error(
                request, "Only superusers are allowed to move blog entries")
            return redirect(
                reverse('admin:cms_blogger_blogentrypage_changelist'))

        def response(form):
            return render_to_response(
                "admin/cms_blogger/blog/move_entries.html",
                {'move_form': form, 'title': 'Move entries'},
                context_instance=RequestContext(request))

        qs = BlogEntryPage.objects.filter(id__in=request.GET.keys())
        if request.method == "GET":
            form = forms.MoveEntriesForm(entries=qs, checked=qs)
            return response(form)

        form = forms.MoveEntriesForm(request.POST, entries=qs, checked=qs)
        if not form.is_valid():
            return response(form)

        post_data = request.POST.copy()
        entries = form.cleaned_data['entries']
        if not entries:
            form = forms.MoveEntriesForm(post_data, entries=qs)
            messages.error(request, "There are no entries selected.")
            return response(form)

        destination_blog = form.cleaned_data['destination_blog']
        valid_entries = entries.exclude(blog=destination_blog)
        valid_entries_ids = list(valid_entries.values_list('id', flat=True))
        redundant_entries = entries.filter(blog=destination_blog)
        post_data.setlist('entries', map(unicode, valid_entries_ids))
        form = forms.MoveEntriesForm(post_data, entries=qs)

        def f(entries, msg, length=100):
            entries_list = ', '.join(entries.values_list('title', flat=True))
            if len(entries_list) > length:
                entries_list = "%s ..." % entries_list[:(length - 4)]
            message = "%s%s%s" % (
                ungettext(
                    'Entry %(entry)s was ', 'Entries %(entry)s were ',
                    entries.count()),
                msg,
                " blog %(blog)s")
            return message % {
                'entry': entries_list,
                'blog': destination_blog}

        if redundant_entries.exists():
            message = f(redundant_entries, 'already present in')
            messages.warning(request, message)
            return response(form)

        _move_entries(
            destination_blog,
            valid_entries_ids,
            'mirror_categories' in form.data)
        message = f(BlogEntryPage.objects.filter(
            id__in=valid_entries_ids),
            'successfully moved to')
        messages.success(request, message)
        return redirect(reverse('admin:cms_blogger_blogentrypage_changelist'))

    ### PLACEHOLDER ADMIN VIEWS ###
    def add_plugin(self, request):
        """
        Adds a plugin the the hidded placeholder of the blog entry.
        Since the placeholder has only one plugin(text plugin) we need to
        set the parent_id in order for all plugins to be added inside the
        text plugin.
        """
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

    ### BULK ACTIONS ###
    def make_published(self, request, queryset):
        # cannot publish draft entries
        draft_entries = Q(Q(title__isnull=True) | Q(title__exact='') |
                          Q(short_description__isnull=True) |
                          Q(short_description__exact='') |
                          Q(blog__isnull=True))
        queryset.exclude(draft_entries).filter(is_published=False).update(
            is_published=True, publication_date=timezone.now())
    make_published.short_description = "Publish entries"

    def make_unpublished(self, request, queryset):
        queryset.filter(is_published=True).update(
            is_published=False, publication_date=timezone.now())
    make_unpublished.short_description = "Unpublish entries"

    def move_entries(self, request, queryset):
        entries = {x: "" for x in request.POST.getlist(
            admin.helpers.ACTION_CHECKBOX_NAME)}
        url = "%s?%s" % (
            reverse('admin:cms_blogger-move-entries'),
            urllib.urlencode(entries))
        return redirect(url)
    move_entries.short_description = "Move entries to another blog"

    ### CUSTOM ADMIN COLUMNS ###
    def entry_authors(self, entry):
        return entry.authors_display_name
    entry_authors.allow_tags = True

    def published_at(self, entry):
        return (
            '<script type="text/javascript">'
            'var str_date = (new Date(moment("%s"))).toString();'
            'document.write(/(.*)GMT|UTC[+-]\d*/g.exec(str_date)[1]);'
            '</script>' % entry.publication_date)
    published_at.allow_tags = True

    def categories_assigned(self, entry):
        category_names = list(entry.categories
            .values_list('name', flat=True).order_by('name'))
        text = ', '.join(category_names)
        max_len = 70
        return text if len(text) <= max_len else (text[:max_len-3] + '...')
    categories_assigned.short_description = 'Categories'

    ### PERMISSIONS ###
    def _is_allowed(self, request):
        if request.user.is_superuser:
            return True
        return Blog.objects.filter(allowed_users=request.user).exists()

    def has_add_permission(self, request):
        can_add = super(BlogEntryPageAdmin, self).has_add_permission(request)
        return can_add and self._is_allowed(request)

    def has_change_permission(self, request, obj=None):
        can_change = super(BlogEntryPageAdmin, self)\
            .has_change_permission(request, obj)
        return can_change and self._is_allowed(request)

    def has_delete_permission(self, request, obj=None):
        can_delete = super(BlogEntryPageAdmin, self)\
            .has_delete_permission(request, obj)
        return can_delete and self._is_allowed(request)


def _move_entries(destination_blog, entries_ids, mirror_categories=True):
    original_categories = list(BlogCategory.objects.filter(
        entries__in=entries_ids).values_list('id', 'name'))
    if original_categories:
        original_categories_ids, original_categories_name = zip(
            *original_categories)
    else:
        original_categories_ids, original_categories_name = [], []

    if mirror_categories:
        destination_categories = list(
            destination_blog.categories.values_list('name', flat=True))
        delta = set(original_categories_name) - set(destination_categories)
        delta = filter(None, delta)
        for category_name in delta:
            BlogCategory.objects.create(
                name=category_name,
                blog=destination_blog)

    # link entries foreign key to the new blog
    entries = BlogEntryPage.objects.filter(id__in=entries_ids)
    entries.update(blog=destination_blog)

    # regenerate slugs for saved entries (which
    # are not draft) to make sure they are unique
    saved_entries_ids = list(
        entries.filter(draft_id=None).values_list('id', flat=True))
    BlogEntryPage.objects.filter(id__in=saved_entries_ids).update(slug="")
    for e in BlogEntryPage.objects.filter(id__in=saved_entries_ids):
        e.save()

    # performance improvement getting previous_categories in dict
    for blogentry in BlogEntryPage.objects.filter(id__in=entries_ids):
        previous_categories = list(blogentry.categories.values_list(
            'name', flat=True))
        #performance improvement by assigning m2m queryset instead of clearing
        # and reassigning
        blogentry.categories.clear()
        destination_categories = BlogCategory.objects.filter(
            blog=destination_blog, name__in=previous_categories)
        blogentry.categories.add(*destination_categories)

    BlogCategory.objects.filter(
        id__in=original_categories_ids, entries=None
    ).delete()


admin.site.register(Blog, BlogAdmin)
admin.site.register(HomeBlog, HomeBlogAdmin)
admin.site.register(BlogEntryPage, BlogEntryPageAdmin)
