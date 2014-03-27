from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
from django.template.defaultfilters import slugify
from django.forms.util import ErrorList
from django.contrib.contenttypes.generic import BaseGenericInlineFormSet
from cms.plugin_pool import plugin_pool
from cms.plugins.text.settings import USE_TINYMCE
from cms.plugins.text.widgets.wymeditor_widget import WYMEditor
from cms.utils.plugins import get_placeholders
from cms.models import Page
from cms_layouts.models import Layout
from cms_layouts.slot_finder import (
    get_fixed_section_slots, MissingRequiredPlaceholder)
from .models import Blog, BlogEntryPage


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


class BlogForm(forms.ModelForm):

    class Meta:
        model = Blog

    def __init__(self, *args, **kwargs):
        super(BlogForm, self).__init__(*args, **kwargs)
        if (not self.is_bound and self.instance and self.instance.pk and
                self.instance.layouts.count() == 0):
            self.missing_layouts = ErrorList([
                "This blog is missing a layout. "
                "Add one in the Layouts section."])
        else:
            self.missing_layouts = False

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


class BlogAddForm(forms.ModelForm):

    class Meta:
        model = Blog
        fields = ('title', 'slug', 'site')


class BlogEntryPageAddForm(forms.ModelForm):

    class Meta:
        model = BlogEntryPage
        fields = ('blog', )


def _get_text_editor_widget():
    installed_plugins = plugin_pool.get_all_plugins()
    plugins = [plugin for plugin in installed_plugins if plugin.text_enabled]

    if USE_TINYMCE and "tinymce" in settings.INSTALLED_APPS:
        from cms.plugins.text.widgets.tinymce_widget import TinyMCEEditor
        return TinyMCEEditor(installed_plugins=plugins)
    else:
        return WYMEditor(installed_plugins=plugins)


class BlogEntryPageChangeForm(forms.ModelForm):
    body = forms.CharField(
        label='Blog Entry', required=True,
        widget=_get_text_editor_widget())

    class Media:
        js = ("cms_blogger/js/jQuery-patch.js",)
        css = {"all": ("cms_blogger/css/entry-change-form.css", )}

    class Meta:
        model = BlogEntryPage
        exclude = ('content', )

    def __init__(self, *args, **kwargs):
        super(BlogEntryPageChangeForm, self).__init__(*args, **kwargs)
        self.fields['body'].initial = self.instance.body
        # prepare for save
        self.instance.draft_id = None

    def clean_body(self):
        body = self.cleaned_data.get('body')
        self.instance.body = body
        return body

    def clean_slug(self):
        slug = slugify(self.cleaned_data.get('slug', ''))
        blog_id = self.instance.blog_id
        try:
            BlogEntryPage.objects.exclude(pk=self.instance.pk).get(
                slug=slug, blog=blog_id, draft_id=None)
        except BlogEntryPage.DoesNotExist:
            pass
        else:
            raise ValidationError("Entry with the same slug already exists.")
        return slug
