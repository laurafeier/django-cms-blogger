from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericRelation
from django.utils.translation import get_language
from django.db.models import signals
from django.dispatch import receiver
from cms.models.fields import PlaceholderField
from cms_layouts.models import LayoutTitle, Layout
from tagging.fields import TagField


class AbstractBlog(models.Model):

    title = models.CharField(
        _("title"), max_length=255, blank=False, null=False,
        help_text=_('This is the name of the blog; it can be modified later; '
                    'it is only exposed to site viewers as part of the Page'
                    ' Title/SEO fields.'))
    slug = models.SlugField(
        _("slug"), help_text=_(
            'This is the URL scheme where the blog will reside; '
            'http://www.sitename.org/blog/BLOG-SLUG/blog-entry-name'))
    site = models.ForeignKey(
        Site, help_text=_('The site for this blog.'), verbose_name=_("site"))
    entries_slugs_with_date = models.BooleanField(
        help_text=_('Select this option if you want your entries to use '
                    'creation date with their slugs; '
                    'http://www.sitename.org/blog/BLOG-SLUG'
                    '/YYYY/MM/DD/blog-entry-name'))
    categories = TagField(
        null=True, blank=True,
        help_text='Use this admin to create a list of categories to organize'
                  ' content in the blog. Each category will create a '
                  'collection page for posts tagged with one of these '
                  'categories.')

    layouts = GenericRelation(Layout)

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
        BIO_PAGE: 'Blog Bio Page'}

    def layout_type_display(self, layout_type):
        return AbstractBlog.LAYOUTS_CHOICES[layout_type]

    def _get_layout_for_type(self, layout_type):
        try:
            return self.layouts.filter(layout_type__in=[
                layout_type, AbstractBlog.ALL]).order_by('-layout_type')[0]
        except IndexError:
            return None

    def get_landing_layout(self):
        return self._get_layout_for_type(AbstractBlog.LANDING_PAGE)

    def get_bio_layout(self):
        return self._get_layout_for_type(AbstractBlog.BIO_PAGE)

    def get_entry_layout(self):
        return self._get_layout_for_type(AbstractBlog.ENTRY_PAGE)

    def get_title_obj(self):
        title = LayoutTitle()
        title.page_title = self.title
        title.slug = self.slug
        return title

    def __unicode__(self):
        return "%s - %s" % (self.title, self.site.name)


class Blog(AbstractBlog):

    def get_layout(self):
        return self.blog.get_landing_layout()

    @property
    def content(self):
        # some content
        return Placeholder.objects.get(id=65613)

    @models.permalink
    def get_absolute_url(self):
        return ('cms_blogger.views.landing_page', (), {
            'blog_slug': self.slug})


class BioPage(models.Model):

    blog = models.ForeignKey(Blog)
    author_name = models.CharField(max_length=255)

    def get_layout(self):
        return self.blog.get_bio_layout()

    @property
    def content(self):
        # some content
        return Placeholder.objects.get(id=65623)

    @property
    def slug(self):
        return self.author_name.lower().replace(' ', '-')

    @models.permalink
    def get_absolute_url(self):
        return ('cms_blogger.views.bio_page', (), {
            'blog_slug': self.blog.slug,
            'author_slug': self.slug})

    def get_title_obj(self):
        title = LayoutTitle()
        title.page_title = self.author_name.title()
        title.slug = self.slug
        return title

    @property
    def site(self):
        return self.blog.site

    def __unicode__(self):
        return self.author_name.title()


class BlogEntry(models.Model):

    blog = models.ForeignKey(Blog)
    title = models.CharField(_('title'), max_length=120)
    slug = models.SlugField(
        _('slug'), max_length=255,
        help_text=_("Used to build the entry's URL."))
    creation_date = models.DateField(
        _('creation date'),
        db_index=True, default=timezone.now,
        help_text=_("Used to build the entry's URL."))
    author = models.CharField(_('Blog Author'), max_length=255)
    abstract = models.TextField(_('Abstract'), blank=True, max_length=400)
    content = PlaceholderField('content', related_name='article_entry')
    start_publication = models.DateTimeField(
        _('start publication'),
        db_index=True, blank=True, null=True,
        help_text=_('Start date of publication.'))
    end_publication = models.DateTimeField(
        _('end publication'),
        db_index=True, blank=True, null=True,
        help_text=_('End date of publication.'))
    is_published = models.BooleanField(_('is published'), blank=True)
    meta_description = models.TextField(_('Description Meta'), blank=True)
    meta_keywords = models.CharField(
        _('Keywords Meta'), blank=True, max_length=120)

    # needed to take care of autogenerated entries with empty title and slug.
    #   a user may have multiple new draft entries which means a user should
    #   be able to have more entries with empty slug and title. In order for
    #   the unique together constraint for title and slug to be valid we'll
    #   add this draft field that will hold a value if the entry is an
    #   autogenerated draft or it will be null if the the entry was edited at
    #   least once
    draft_id = models.IntegerField(blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super(BlogEntry, self).__init__(*args, **kwargs)
        text_plugin = self.get_text_instance()
        self.body = getattr(text_plugin, 'body', 'Sample entry text')

    def get_layout(self):
        return self.blog.get_entry_layout()

    def get_title_obj(self):
        title = LayoutTitle()
        title.page_title = self.title
        title.slug = self.slug
        title.meta_description = self.meta_description
        title.meta_keywords = self.meta_keywords
        return title

    @models.permalink
    def get_absolute_url(self):
        if self.blog.entries_slugs_with_date:
            return ('cms_blogger.views.entry_page', (), {
                'blog_slug': self.blog.slug,
                'year': self.creation_date.year,
                'month': self.creation_date.strftime('%m'),
                'day': self.creation_date.strftime('%d'),
                'entry_slug': self.slug})
        return ('cms_blogger.views.entry_or_bio_page', (), {
            'blog_slug': self.blog.slug,
            'slug': self.slug})

    @property
    def site(self):
        return self.blog.site

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, value):
        self._body = value

    def get_text_instance(self):
        if not self.content or not self.content.get_plugins():
            return None
        first_plugin = self.content.get_plugins()[0]
        plg_instance, plg_cls = first_plugin.get_plugin_instance()
        return plg_instance

    class Meta:
        verbose_name = "blog entries"
        verbose_name_plural = 'blog entries'
        unique_together = (("slug", "blog", "draft_id"),)

    def __unicode__(self):
        return self.title or "<Draft Empty Blog Entry>"


@receiver(signals.post_save, sender=Blog)
def autogenerate_layout_from_home_page(instance, **kwargs):
    is_new_blog = kwargs.get('created')
    if is_new_blog and instance.layouts.count() == 0:
        from cms.models import Page
        # this might fail but there's already validation in the blog add form
        cms_home_page = Page.objects.get_home(instance.site)
        default_layout = Layout.objects.create(
            from_page=cms_home_page, layout_type=Blog.ALL,
            content_object=instance)


@receiver(signals.post_save, sender=BlogEntry)
def autogenerate_draft_if_new(instance, **kwargs):
    is_new_entry = kwargs.get('created')
    placeholder = instance.content
    entry_as_queryset = BlogEntry.objects.filter(pk=instance.pk)
    if is_new_entry:
        # set draft_id with the same value as the pk to make sure it's unique
        instance.draft_id = instance.pk
        # do an update in order to not trigger save signals
        entry_as_queryset.update(draft_id=instance.pk)
        # add text plugin to the placeholder
        if placeholder and not placeholder.get_plugins():
            from cms.api import add_plugin
            add_plugin(placeholder, 'TextPlugin', get_language(),
                       body=instance.body)
    else:
        # do not mark it as not draft until it has a slug and a blog assigned
        # draft_id is set to None in the change form also but it's good to
        #   have this here too in order to make sure that entries created
        #   programmatically will behave in the same way
        if instance.draft_id and instance.slug and instance.blog_id:
            entry_as_queryset.update(draft_id=None)
        # save text plugin body
        text_plugin = instance.get_text_instance()
        if text_plugin:
            text_plugin.body = instance.body
            text_plugin.save()
