from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.conf import settings
from django.template.defaultfilters import slugify
from django.forms.util import ErrorList
from django.contrib.contenttypes.generic import BaseGenericInlineFormSet
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import router

from cms.plugin_pool import plugin_pool
from cms.plugins.text.settings import USE_TINYMCE
from cms.plugins.text.widgets.wymeditor_widget import WYMEditor
from cms.utils.plugins import get_placeholders
from cms.models import Page

from cms_layouts.models import Layout
from cms_layouts.slot_finder import (
    get_fixed_section_slots, MissingRequiredPlaceholder)

from django_select2.fields import (
    AutoModelSelect2MultipleField, AutoModelSelect2TagField)

from .models import Blog, BlogEntryPage, BlogCategory, Author
from .widgets import TagItWidget, ButtonWidget, DateTimeWidget, PosterImage
from .utils import user_display_name
from cms.templatetags.cms_admin import admin_static_url


class BlogLayoutInlineFormSet(BaseGenericInlineFormSet):

    def clean(self):
        if any(self.errors):
            return
        data = self.cleaned_data
        data_to_delete = filter(lambda x: x.get('DELETE', False), data)
        data = filter(lambda x: not x.get('DELETE', False), data)

        if len(data) < 1:
            raise ValidationError('At least one layout is required!')

        if len(data) > len(Blog.LAYOUTS_CHOICES):
            raise ValidationError(
                'There can be a maximum of %d layouts.' % \
                    len(Blog.LAYOUTS_CHOICES))

        submitted_layout_types = [layout.get('layout_type')
                                  for layout in data]

        if len(submitted_layout_types) != len(set(submitted_layout_types)):
            raise ValidationError(
                "You can have only one layout for each layout type.")

        specific_layout_types = [layout_type
            for layout_type in Blog.LAYOUTS_CHOICES.keys()
            if layout_type != Blog.ALL]

        if Blog.ALL not in submitted_layout_types:
            # check if there are layouts for all of the rest types
            if not all([specific_layout_type in submitted_layout_types
                        for specific_layout_type in specific_layout_types]):
                pretty_specific_layout_types = (
                    Blog.LAYOUTS_CHOICES[layout_type]
                    for layout_type in specific_layout_types)
                raise ValidationError(
                    "If you do not have a layout for %s you need to specify "
                    "a layout for all the rest layout types: %s" % (
                        Blog.LAYOUTS_CHOICES[Blog.ALL],
                        ', '.join(pretty_specific_layout_types)))


class BlogLayoutForm(forms.ModelForm):
    layout_type = forms.IntegerField(
        label='Layout Type',
        widget=forms.Select(choices=Blog.LAYOUTS_CHOICES.items()))
    from_page = forms.IntegerField(
        label='Inheriting layout from page', widget=forms.Select())

    class Meta:
        model = Layout
        fields = ('layout_type', 'from_page')

    def clean_layout_type(self):
        layout_type = self.cleaned_data.get('layout_type', None)
        if layout_type == None:
            raise ValidationError("Layout Type required")
        if layout_type not in Blog.LAYOUTS_CHOICES.keys():
            raise ValidationError(
                "Not a valid Layout Type. Valid choices are: %s" % (
                    ', '.join(Blog.LAYOUTS_CHOICES.values())))
        return layout_type

    def clean_from_page(self):
        from_page_id = self.cleaned_data.get('from_page', None)
        if not from_page_id:
            raise ValidationError('Select a page for this layout.')
        try:
            page = Page.objects.get(id=from_page_id)
        except Page.DoesNotExist:
            raise ValidationError(
                'This page does not exist. Refresh this form and select an '
                'existing page.')
        try:
            slots = get_placeholders(page.get_template())
            fixed_slots = get_fixed_section_slots(slots)
            return page
        except MissingRequiredPlaceholder, e:
            raise ValidationError(
                "Page %s is missing a required placeholder "
                "named %s. Choose a different page for this layout that"
                " has the required placeholder or just add this "
                "placeholder in the page template." % (page, e.slot, ))
        except Exception, page_exception:
            raise ValidationError(
                "Error found while scanning template from page %s: %s. "
                "Change page with a valid one or fix this error." % (
                    page, page_exception))


class MultipleUserField(AutoModelSelect2MultipleField):
    search_fields = ['first_name__icontains', 'last_name__icontains',
                     'email__icontains', 'username__icontains']
    queryset = User.objects.all()
    empty_values = [None, '', 0]

    def label_from_instance(self, obj):
        return user_display_name(obj)


class BlogForm(forms.ModelForm):
    categories = forms.CharField(
        widget=TagItWidget(attrs={
            'tagit': '{allowSpaces: true, tagLimit: 20, '
                     'caseSensitive: false}'}),
        help_text=_('Categories help text'))

    allowed_users = MultipleUserField(label="Add Users")

    class Meta:
        model = Blog

    def __init__(self, *args, **kwargs):
        super(BlogForm, self).__init__(*args, **kwargs)
        self._init_categories_field(self.instance)
        if (not self.is_bound and self.instance.layouts.count() == 0):
            self.missing_layouts = ErrorList([
                "This blog is missing a layout. "
                "Add one in the Layouts section."])
        else:
            self.missing_layouts = False

    def _init_categories_field(self, blog):
        categories_field = self.fields.get('categories', None)
        if blog and blog.pk and not categories_field.initial:
            categories_field.initial = ', '.join(
                blog.categories.values_list('name', flat=True))

    def clean_categories(self):
        categories = self.cleaned_data.get('categories', '')
        if not categories:
            raise ValidationError("Add at least one category.")

        categories_names = [name.strip().lower()
                            for name in categories.split(',')]
        return categories_names

    def clean_in_navigation(self):
        in_navigation = self.cleaned_data.get('in_navigation', False)
        if in_navigation:
            if not self.instance.navigation_node:
                raise ValidationError(
                    "Choose a location in the navigation menu")
        return in_navigation

    def clean_slug(self):
        return slugify(self.cleaned_data.get('slug', ''))

    def clean_disqus_shortname(self):
        disqus_enabled = self.cleaned_data.get('enable_disqus', None)
        disqus_shortname = self.cleaned_data.get('disqus_shortname', None)
        if disqus_enabled and not disqus_shortname:
            raise ValidationError('Disqus shortname required.')
        return disqus_shortname

    def _save_categories(self, saved_blog):
        names = set(self.cleaned_data.get('categories', []))
        existing_names = set(saved_blog.categories.values_list(
            'name', flat=True))
        removed_categories = existing_names - names
        new_category_names = names - existing_names

        for name in new_category_names:
            BlogCategory.objects.create(name=name, blog=saved_blog)

        for category in BlogCategory.objects.filter(
                name__in=removed_categories, blog=saved_blog):
            category.delete()

    def save(self, commit=True):
        saved_instance = super(BlogForm, self).save(commit=commit)
        if commit:
            self._save_categories(saved_instance)
        else:
            original_save_m2m = self.save_m2m
            if not hasattr(original_save_m2m, '_save_categories_attached'):
                def _extra_save_m2m():
                    self._save_categories(saved_instance)
                    original_save_m2m()
                self.save_m2m = _extra_save_m2m
                setattr(self.save_m2m, '_save_categories_attached', True)

        return saved_instance


class BlogAddForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        site_field = self.base_fields['site']
        site_field.choices = []
        site_field.widget = forms.HiddenInput()
        site_field.initial = Site.objects.get_current().pk
        super(BlogAddForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Blog
        fields = ('title', 'slug', 'site')


class EntryChangelistForm(forms.ModelForm):

    is_published = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={
            'onclick': (
                "jQuery(this).closest('form').append("
                "jQuery('<input>').attr('type', 'hidden').attr("
                    "'name', '_save').val('Save')"
                ").submit();")
            }))

    def __init__(self, *args, **kwargs):
        entry = kwargs.get('instance', None)
        pub_field = self.base_fields['is_published']
        if entry and entry.is_draft:
            pub_field.widget.attrs['disabled'] = 'disabled'
        else:
            pub_field.widget.attrs.pop('disabled', None)
        super(EntryChangelistForm, self).__init__(*args, **kwargs)

    def clean_is_published(self):
        is_published = self.cleaned_data.get('is_published')
        if not self.instance:
            return is_published

        if is_published != self.instance.is_published:
            if not is_published:
                self.instance.start_publication = None
                self.instance.end_publication = None

            self.instance.publication_date = timezone.now()
        return is_published

    class Meta:
        model = BlogEntryPage


class BlogEntryPageAddForm(forms.ModelForm):
    requires_request = True

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        # filter available blog choices
        site = Site.objects.get_current()
        blog_field = self.base_fields['blog']
        allowed_blogs = blog_field.queryset.filter(site=site)
        if request and not request.user.is_superuser:
            allowed_blogs = allowed_blogs.filter(
                allowed_users=request.user)
        blog_field.queryset = allowed_blogs
        blog_field.widget.can_add_related = False
        super(BlogEntryPageAddForm, self).__init__(*args, **kwargs)

    class Meta:
        model = BlogEntryPage
        fields = ('blog', )


def _get_text_editor_widget():
    installed_plugins = plugin_pool.get_all_plugins()
    plugins = [plugin for plugin in installed_plugins if plugin.text_enabled]

    if USE_TINYMCE and "tinymce" in settings.INSTALLED_APPS:
        from cms.plugins.text.widgets.tinymce_widget import TinyMCEEditor
        return TinyMCEEditor(installed_plugins=plugins, mce_attrs={
            'theme_advanced_buttons1': (
                'forecolor, bold, italic, underline, link, unlink, numlist, '
                'bullist, outdent, indent, formatselect, image, code'),
            'theme_advanced_buttons2_add': (
                'justifyleft, justifycenter, justifyright, justifyfull,'
                'fontselect, fontsizeselect'),
            'theme_advanced_buttons3_add': (
                'strikethrough, sub, sup, fullscreen'),
            'theme_advanced_toolbar_location': 'top',
            'theme_advanced_toolbar_align': 'left',
            'setup' : 'tinyMCESetup'
            })
    else:
        return WYMEditor(installed_plugins=plugins)


class ButtonField(forms.Field):

    def __init__(self, *args, **kwargs):
        kwargs["label"] = ""
        kwargs["required"] = False
        super(ButtonField, self).__init__(*args, **kwargs)


class AuthorsField(AutoModelSelect2TagField):
    queryset = Author.objects.db_manager(router.db_for_write(Author))
    empty_values = [None, '', 0]
    search_fields = ['name__icontains', 'user__first_name__icontains',
                     'user__last_name__icontains', 'user__email__icontains',
                     'user__username__icontains']

    def get_model_field_values(self, value):
        return {'name': value}

    def make_authors(self):
        # since this is a GET request and it does a db updates, ensure it
        #   uses the 'write' db for reads also
        author_mgr = Author.objects.db_manager(router.db_for_write(Author))
        user_mgr = User.objects.db_manager(router.db_for_write(User))
        users_used = author_mgr.values_list('user', flat=True)
        candidates_for_author = user_mgr.exclude(id__in=users_used)
        for user in candidates_for_author:
            author_mgr.get_or_create(name='', user=user)
        return author_mgr.all()

    def __init__(self, *args, **kwargs):
        self.make_authors()
        super(AuthorsField, self).__init__(*args, **kwargs)


class BlogEntryPageChangeForm(forms.ModelForm):
    requires_request = True

    body = forms.CharField(
        label='Blog Entry', required=True,
        widget=_get_text_editor_widget())
    authors = AuthorsField()
    poster_image_uploader = forms.CharField(label="", widget=PosterImage())
    categories = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        help_text=_("Check all the categories to apply to this post. Uncheck to remove."),
        queryset=BlogCategory.objects.get_empty_query_set(), required=False)

    publish = ButtonField(widget=ButtonWidget(submit=True,
        on_click=("jQuery(this).closest('form').append("
                  "jQuery('<input>').attr('type', 'hidden').attr("
                    "'name', '_pub_pressed').val(true)"
                  ");")))

    schedule_publish = ButtonField(widget=ButtonWidget(
        attrs={'style': 'float: right'},
        submit=True, text='Schedule Publish',
        on_click=("jQuery(this).closest('form').append("
                  "jQuery('<input>').attr('type', 'hidden').attr("
                    "'name', '_schedule_pub_pressed').val(true)"
                  ");")))
    schedule_unpublish = ButtonField(widget=ButtonWidget(
        attrs={'style': 'float: right'},
        submit=True, text='Schedule Unpublish',
        on_click=("jQuery(this).closest('form').append("
                  "jQuery('<input>').attr('type', 'hidden').attr("
                    "'name', '_schedule_unpub_pressed').val(true)"
                  ");")))

    start_publication = forms.Field(
        required=False, widget=DateTimeWidget())
    end_publication = forms.Field(
        required=False, widget=DateTimeWidget())

    save_button = ButtonField(widget=ButtonWidget(submit=True, text='Save'))
    preview_on_top = ButtonField(widget=ButtonWidget(text='Preview'))
    preview_on_bottom = ButtonField(widget=ButtonWidget(text='Preview'))

    class Media:
        css = {"all": ("cms_blogger/css/entry-change-form.css",
                       "cms_blogger/css/jquery.fs.scroller.css" )}
        js = ('cms_blogger/js/tinymce-extend.js',
              'cms_blogger/js/entry-admin.js',
              'cms_blogger/js/jquery.fs.scroller.js',
              'cms_blogger/js/admin-collapse.js',
              'cms_blogger/js/entry-preview.js', )


    class Meta:
        model = BlogEntryPage
        exclude = ('content', 'blog', 'slug', 'publication_date')

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        instance = kwargs.get('instance')
        self._init_categ_field(instance) if instance else ''
        super(BlogEntryPageChangeForm, self).__init__(*args, **kwargs)
        self._init_preview_buttons()
        self._init_poster_image_widget()
        self._init_publish_button()
        if request and self.instance.authors.count() == 0:
            self.initial['authors'] = Author.objects.filter(
                name='', user=request.user.pk)[:1]

        self.fields['body'].initial = self.instance.content_body
        # prepare for save
        self.instance.draft_id = None

    def _init_categ_field(self, entry):
        categories_field = self.base_fields.get('categories')
        if categories_field and entry.blog:
            categories_field.queryset = entry.blog.categories.all()
            categories_field.initial = entry.categories.all()

    def _init_publish_button(self):
        pub_button = self.fields['publish'].widget
        if self.instance.is_published:
            pub_button.text = 'Unpublish'
        else:
            pub_button.text = 'Publish Now'

    def _init_preview_buttons(self):
        preview1 = self.fields['preview_on_top'].widget
        preview2 = self.fields['preview_on_bottom'].widget
        url = reverse('admin:cms_blogger-entry-preview',
            args=[self.instance.id])
        preview1.link_url = preview2.link_url = url
        popup_js = "return showEntryPreviewPopup(this,'%s');" % admin_static_url()
        preview1.on_click = preview2.on_click = popup_js

    def _init_poster_image_widget(self):
        poster_widget = self.fields['poster_image_uploader'].widget
        poster_widget.blog_entry_id = self.instance.pk
        poster_widget.image_url = None
        if self.instance.poster_image and self.instance.poster_image.name:
            poster_widget.image_url = self.instance.poster_image.url

    def clean_body(self):
        body = self.cleaned_data.get('body')
        self.instance.content_body = body
        return body

    def clean_title(self):
        title = self.cleaned_data.get('title').strip()
        slug = slugify(title)
        entries_with_slug = BlogEntryPage.objects.filter(
            blog=self.instance.blog, draft_id=None, slug=slug)
        if entries_with_slug.exclude(pk=self.instance.pk).exists():
            raise ValidationError(
                "Entry with the same slug already exists. "
                "Choose a different title.")
        return title

    def _set_publication_date(self):
        publish_toggle = bool(self.data.get('_pub_pressed'))
        if publish_toggle:
            self.instance.is_published = not self.instance.is_published
        elif (bool(self.data.get('_schedule_pub_pressed')) or
                bool(self.data.get('_schedule_unpub_pressed'))):
            self.instance.is_published = True

        now = timezone.now()
        if not self.instance.is_published:
            # entry got unpublished
            self.cleaned_data['start_publication'] = None
            self.cleaned_data['end_publication'] = None
            self.instance.publication_date = now
            return

        start_date = self.cleaned_data.get('start_publication')
        if start_date != self.instance.start_publication:
            self.instance.publication_date = start_date or now

    def clean(self):
        start_date = self.cleaned_data.get('start_publication')
        end_date = self.cleaned_data.get('end_publication')
        if (start_date and end_date and not start_date < end_date):
            raise ValidationError("Incorrect publication dates interval.")
        self._set_publication_date()
        return self.cleaned_data

    def _save_categories(self, saved_entry):
        submitted_categories = self.cleaned_data.get('categories', [])
        blog = saved_entry.blog
        saved_entry.categories.clear()
        if blog:
            saved_entry.categories = blog.categories.filter(
                pk__in=submitted_categories)

    def save(self, commit=True):
        saved_instance = super(BlogEntryPageChangeForm, self).save(
            commit=commit)
        if commit:
            self._save_categories(saved_instance)
        else:
            original_save_m2m = self.save_m2m
            if not hasattr(original_save_m2m, '_save_categories_attached'):
                def _extra_save_m2m():
                    self._save_categories(saved_instance)
                    original_save_m2m()
                self.save_m2m = _extra_save_m2m
                setattr(self.save_m2m, '_save_categories_attached', True)
        return saved_instance
