from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericRelation
from django.utils.translation import get_language
from django.template.defaultfilters import slugify
from django.template import Context
from django.template.loader import get_template
from django.db.models import signals
from django.dispatch import receiver
from django.http import HttpResponseNotFound

from cms.models.fields import PlaceholderField
from cms.models import Page, Placeholder, CMSPlugin

from cms_layouts.models import LayoutTitle, Layout
from cms_layouts.layout_response import LayoutResponse
from filer.fields.image import FilerImageField
import filer
from .utils import user_display_name
from .managers import EntriesManager


def getCMSContentModel(**kwargs):
    content_attr = kwargs.get('content_attr', 'content')
    body_attr = '%s_body' % content_attr
    plugin_getter = 'get_%s_plugin' % content_attr

    class ModelWithCMSContent(models.Model):

        def __init__(self, *args, **kwargs):
            super(ModelWithCMSContent, self).__init__(*args, **kwargs)
            # initialize text plugin body
            setattr(self, body_attr, 'Sample content')
            plugin = getattr(self, plugin_getter)()
            if self.pk and plugin:
                setattr(self, body_attr, getattr(plugin, 'body'))

        def save(self, *args, **kwargs):
            super(ModelWithCMSContent, self).save(*args, **kwargs)
            plugin = getattr(self, plugin_getter)()
            plugin_data = getattr(self, body_attr)
            if plugin and plugin.body != plugin_data:
                plugin.body = plugin_data
                plugin.save()

        class Meta:
            abstract = True

    def get_attached_plugin(instance):
        try:
            placeholder = getattr(instance, content_attr)
        except Placeholder.DoesNotExist:
            return None
        if not placeholder:
            return None
        if not placeholder.get_plugins():
            from cms.api import add_plugin
            new_plugin = add_plugin(
                placeholder, 'TextPlugin', get_language(),
                body=getattr(instance, body_attr))
            return new_plugin
        first_plugin = placeholder.get_plugins()[0]
        plg_instance, plg_cls = first_plugin.get_plugin_instance()
        return plg_instance

    # set content placeholder field
    ModelWithCMSContent.add_to_class(
        content_attr, PlaceholderField(content_attr))
    # set body property
    ModelWithCMSContent.add_to_class(
        body_attr,
        property(lambda x: getattr(x, "_%s" % body_attr),
                 lambda x, v: setattr(x, "_%s" % body_attr, v))
        )
    ModelWithCMSContent.add_to_class(plugin_getter, get_attached_plugin)
    return ModelWithCMSContent


class AbstractBlog(models.Model):

    title = models.CharField(
        _('title'), max_length=255, blank=False, null=False,
        help_text=_('Blog Title'))
    slug = models.SlugField(
        _("slug"), help_text=_('Blog Slug'))
    site = models.ForeignKey(
        Site, help_text=_('Blog Site'), verbose_name=_("site"))
    entries_slugs_with_date = models.BooleanField(
        _("Dates in blog entry URLs"),
        help_text=_('Blog Entries With Slugs'))

    layouts = GenericRelation(Layout)

    allowed_users = models.ManyToManyField(User, verbose_name=_("Add Users"))

    class Meta:
        unique_together = (("slug", "site"),)
        abstract = True

    # values that are used distinguish layout types for this blog
    ALL = 0
    LANDING_PAGE = 1
    ENTRY_PAGE = 2
    BIO_PAGE = 3

    LAYOUTS_CHOICES = {
        ALL: 'All Blog-related Page Layouts',
        LANDING_PAGE: 'Blog Landing Page',
        ENTRY_PAGE: 'Blog Entry Page',
        # BIO_PAGE: 'Blog Bio Page'
    }

    def get_layout_for(self, layout_type):
        if layout_type not in AbstractBlog.LAYOUTS_CHOICES.keys():
            raise NotImplementedError
        try:
            return self.layouts.filter(layout_type__in=[
                layout_type, AbstractBlog.ALL]).order_by('-layout_type')[0]
        except IndexError:
            return None

    def get_title_obj(self):
        title = LayoutTitle()
        title.page_title = self.title
        title.slug = self.slug
        return title

    def __unicode__(self):
        return "%s - %s" % (self.title, self.site.name)


class BlogNavigationNode(models.Model):
    # menu text button
    text = models.CharField(max_length=15)
    # position index in child nodes
    position = models.PositiveIntegerField()
    # parent navigation node id (blog nav nodes will have negative integers
    #  in order to not have id clashes with the ones from pages)
    parent_node_id = models.IntegerField(blank=True, null=True, db_index=True)
    modified_at = models.DateTimeField(auto_now=True, db_index=True)

    @property
    def blog(self):
        attached_blog = self.blog_set.all()[:1]
        return attached_blog[0] if attached_blog else None

    def get_absolute_url(self):
        return self.blog.get_absolute_url() if self.blog else ''

    def is_visible(self):
        return self.blog.in_navigation if self.blog else False


class Blog(AbstractBlog):
    # definitions of the blog model features go here

    # header metadata
    tagline = models.CharField(
        _('tagline'), max_length=60, blank=True, null=True,
        help_text=_('Blog Tagline'))
    branding_image = FilerImageField(
        null=True, blank=True, on_delete=models.SET_NULL,
        default=None, help_text=_('Blog Branding Image'))

    # blog navigation
    in_navigation = models.BooleanField(
        _('Add blog to navigation'), default=False,
        help_text=_('Blog navigation'))
    navigation_node = models.ForeignKey(
        BlogNavigationNode, null=True, blank=True, on_delete=models.SET_NULL)

    # social media integration
    enable_facebook = models.BooleanField(
        _('Facebook integration'), default=True,
        help_text=_('Blog Facebook integration'))
    enable_twitter = models.BooleanField(
        _('Twitter integration'), default=True,
        help_text=_('Blog Twitter integration'))
    email_account_link = models.BooleanField(
        default=True,
        help_text=_('Blog Email integration'))

    # disqus integration
    enable_disqus = models.BooleanField(default=False)
    disqus_shortname = models.CharField(
        max_length=255, blank=True, null=True,
        help_text=_('Blog Disqus Shortname'))
    disable_disqus_for_mobile = models.BooleanField(
        _('DISABLE Disqus commenting at mobile breakpoints (<480)'),
        default=False,
        help_text=_(
            'Select ON to hide comments on phone sized mobile devices.'))

    @property
    def attached_image(self):
        try:
            return self.branding_image
        except filer.models.Image.DoesNotExist:
            return None

    def render_header(self, request, context):
        return get_template("cms_blogger/blog_header.html").render(context)

    def get_entries(self):
        ordering = ('-publication_date', 'slug')
        return self.blogentrypage_set.published().order_by(*ordering)

    def render_content(self, request, context):
        # landing page view passes entries, blog to the context
        return get_template("cms_blogger/blog_content.html").render(context)

    @models.permalink
    def get_absolute_url(self):
        return ('cms_blogger.views.landing_page', (), {
            'blog_slug': self.slug})

    def get_layout(self):
        return self.get_layout_for(Blog.LANDING_PAGE)


def withBlogField(cls):
    # adds a blog foreign key(with a related name if specified) to a model
    # blog foreign key is required by all blog related pages.
    blog = models.ForeignKey(
        Blog, related_name=getattr(cls, 'blog_related_name', None))
    cls.add_to_class('blog', blog)
    return cls


class BlogRelatedPage(object):
    # any blog related pages needs to have a layout, a content and a header
    #   that can be rendered by the layout
    uses_layout_type = None

    def get_layout(self):
        return self.blog.get_layout_for(self.uses_layout_type)

    def render_header(self, request, context):
        return self.blog.render_header(request, context)

    def render_content(self, request, context):
        return self.blog.render_content(request, context)

    @property
    def site(self):
        return self.blog.site

    def get_title_obj(self):
        raise NotImplementedError

    def get_absolute_url(self):
        raise NotImplementedError


@withBlogField
class BioPage(models.Model, BlogRelatedPage):

    uses_layout_type = Blog.BIO_PAGE
    author_name = models.CharField(max_length=255)

    @property
    def slug(self):
        return slugify(self.author_name)

    @models.permalink
    def get_absolute_url(self):
        return ('cms_blogger.views.entry_or_bio_page', (), {
            'blog_slug': self.blog.slug,
            'slug': self.slug})

    def get_title_obj(self):
        title = LayoutTitle()
        title.page_title = self.author_name.title()
        title.slug = self.slug
        return title

    def __unicode__(self):
        return self.author_name.title()


def upload_entry_image(instance, filename):
    import os
    filename_base, filename_ext = os.path.splitext(filename)
    return 'blog/%s%s' % (
        timezone.now().strftime("%Y%m%d%H%M%S"),
        filename_ext.lower(),
    )


@withBlogField
class BlogEntryPage(
    getCMSContentModel(content_attr='content'), BlogRelatedPage):

    uses_layout_type = Blog.ENTRY_PAGE

    title = models.CharField(_('title'), max_length=120)
    slug = models.SlugField(
        _('slug'), max_length=255,
        help_text=_("Used to build the entry's URL."))
    publication_date = models.DateTimeField(
        _('publication date'),
        db_index=True, default=timezone.now,
        help_text=_("Used to build the entry's URL."))
    modified_at = models.DateTimeField(auto_now=True, db_index=True)

    thumbnail_image = models.ImageField(
        _("Thumbnail Image"), upload_to=upload_entry_image, blank=True)

    author = models.ForeignKey(
        User, verbose_name=_('Blog Entry Author'),
        null=True, blank=True, on_delete=models.SET_NULL)

    short_description = models.TextField(
        _('Short Description'), help_text=_("400 characters or fewer"),
        max_length=400)

    start_publication = models.DateTimeField(
        _('start publication'),
        db_index=True, blank=True, null=True,
        help_text=_('Start date of publication.'))
    end_publication = models.DateTimeField(
        _('end publication'),
        db_index=True, blank=True, null=True,
        help_text=_('End date of publication.'))
    is_published = models.BooleanField(_('is published'), blank=True)

    seo_title = models.CharField(
        _('SEO Title'), blank=True, max_length=120)
    meta_keywords = models.CharField(
        _('Keywords Meta'), blank=True, max_length=120)
    disqus_enabled = models.BooleanField(
        _('Disqus integration'), default=True,
        help_text=_('Set OFF to disable commenting for this entry.'))

    # needed to take care of autogenerated entries with empty title and slug.
    #   a user may have multiple new draft entries which means a user should
    #   be able to have more entries with empty slug and title. In order for
    #   the unique together constraint for title and slug to be valid we'll
    #   add this draft field that will hold a value if the entry is an
    #   autogenerated draft or it will be null if the the entry was edited at
    #   least once
    draft_id = models.IntegerField(blank=True, null=True)

    objects = EntriesManager()

    @property
    def is_draft(self):
        if all([self.title, self.short_description, self.slug, self.blog_id]):
            return False
        return True

    @property
    def author_display_name(self):
        if not self.author:
            return ''
        return user_display_name(self.author)

    def extra_html_before_content(self, request, context):
        if not self.blog:
            return ''
        return get_template("cms_blogger/entry_top.html").render(context)

    def extra_html_after_content(self, request, context):
        if not self.blog:
            return ''
        return get_template("cms_blogger/entry_bottom.html").render(context)

    def get_title_obj(self):
        title = LayoutTitle()
        title.title = self.title
        title.page_title = self.seo_title
        title.slug = self.slug
        title.short_description = self.short_description
        title.meta_keywords = self.meta_keywords
        return title

    @models.permalink
    def get_absolute_url(self):
        if self.blog.entries_slugs_with_date:
            return ('cms_blogger.views.entry_page', (), {
                'blog_slug': self.blog.slug,
                'year': self.publication_date.year,
                'month': self.publication_date.strftime('%m'),
                'day': self.publication_date.strftime('%d'),
                'entry_slug': self.slug})
        return ('cms_blogger.views.entry_or_bio_page', (), {
            'blog_slug': self.blog.slug,
            'slug': self.slug})

    def render_to_response(self, request):
        layout = self.get_layout()
        if not layout:
            return HttpResponseNotFound(
                "<h1>This Entry does not have a layout to render.</h1>")
        from django.template.context import RequestContext
        context = RequestContext(request)
        context.update({'entry': self, 'blog': self.blog,})
        return LayoutResponse(
            self, layout, request, context=context).make_response()

    def previous_post(self):
        if not self.blog:
            return None
        query_for_prev = Q(
            Q(Q(publication_date=self.publication_date) &
              Q(slug__lt=self.slug)) |
            Q(publication_date__lt=self.publication_date))
        prev_post = self.blog.get_entries().exclude(
            id=self.id).filter(query_for_prev)[:1]
        if prev_post:
            return prev_post[0]
        return None

    def next_post(self):
        if not self.blog:
            return None
        query_for_next = Q(
            Q(Q(publication_date=self.publication_date) &
              Q(slug__gt=self.slug)) |
            Q(publication_date__gt=self.publication_date))
        next_post = self.blog.get_entries().exclude(
            id=self.id).filter(query_for_next)[:1]
        if next_post:
            return next_post[0]
        return None


    class Meta:
        verbose_name = "blog entry"
        verbose_name_plural = 'blog entries'
        unique_together = (("slug", "blog", "draft_id"),)

    def __unicode__(self):
        return "<Draft Empty Blog Entry>" if self.is_draft else self.title


@withBlogField
class BlogCategory(models.Model, BlogRelatedPage):
    blog_related_name = 'categories'
    name = models.CharField(_('name'), max_length=30, db_index=True)
    slug = models.SlugField(_('slug'), max_length=60)
    blog_entry = models.ForeignKey(BlogEntryPage, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='categories')

    @models.permalink
    def get_absolute_url(self):
        return ('cms_blogger.views.category_page', (), {
            'blog_slug': self.blog.slug,
            'slug': self.slug})

    def get_title_obj(self):
        title = LayoutTitle()
        title.page_title = self.name
        title.slug = self.slug
        return title

    def get_entries(self):
        return BlogEntryPage.objects.published().filter(
            blog=self.blog, categories=self)

    def get_layout(self):
        return self.blog.get_layout_for(Blog.LANDING_PAGE)

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = (("slug", 'blog'),)


class BlogPromotion(CMSPlugin):

    blog = models.ForeignKey(Blog)
    blog_title = models.BooleanField(default=True)
    blog_tagline = models.BooleanField(default=True)
    branding_image = models.BooleanField(default=True)

    display_abstract = models.BooleanField(default=True)
    display_thumbnails = models.BooleanField(default=True)
    number_of_entries = models.PositiveIntegerField(
        _('Entries to Display'), default=10)


@receiver(signals.post_save, sender=BlogEntryPage)
def mark_draft(instance, **kwargs):
    is_new_entry = kwargs.get('created')
    entry_as_queryset = BlogEntryPage.objects.filter(pk=instance.pk)
    if is_new_entry:
        # set draft_id with the same value as the pk to make sure it's unique
        instance.draft_id = instance.pk
        # do an update in order to not trigger save signals
        entry_as_queryset.update(draft_id=instance.pk)
    else:
        # do not mark it as not draft until it has a slug and a blog assigned
        # draft_id is set to None in the change form also but it's good to
        #   have this here too in order to make sure that entries created
        #   programmatically will behave in the same way
        if instance.draft_id and not instance.is_draft:
            entry_as_queryset.update(draft_id=None)
