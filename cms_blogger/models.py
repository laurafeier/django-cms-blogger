from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from cms.models.fields import PlaceholderField
from cms_layouts.models import LayoutTitle, Layout
from tagging.fields import TagField


class AbstractBlog(models.Model):

    title = models.CharField(_("title"), max_length=255,
        blank=False, null=False,
        help_text=_('This is the name of the blog; it can be modified later; '
                    'it is only exposed to site viewers as part of the Page'
                    ' Title/SEO fields.'))
    slug = models.SlugField(_("slug"),
        unique=False, help_text=_(
            'This is the URL scheme where the blog will reside; '
            'http://www.sitename.org/blog/BLOG-SLUG/blog-entry-name'))
    site = models.ForeignKey(Site,
        help_text=_('The site for this blog.'), verbose_name=_("site"))
    categories = TagField(null=True, blank=True,
        help_text='Use this admin to create a list of categories to organize'
                  ' content in the blog. Each category will create a '
                  'collection page for posts tagged with one of these '
                  'categories.')

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

    @property
    def layouts(self):
        if not self.pk:
            return Layout.objects.get_empty_query_set()
        ct = ContentType.objects.get_for_model(self._meta.concrete_model)
        return Layout.objects.filter(object_id=self.id, content_type=ct)

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
        return self.title


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
    slug = models.SlugField(_('slug'), max_length=255,
        unique_for_date='creation_date',
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
    meta_keywords = models.CharField(_('Keywords Meta'), blank=True, max_length=120)

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
        return ('cms_blogger.views.entry_page', (), {
            'year': self.creation_date.year,
            'month': self.creation_date.strftime('%m'),
            'day': self.creation_date.strftime('%d'),
            'entry_slug': self.slug})

    @property
    def site(self):
        return self.blog.site

    def get_text_instance(self):
        if not self.content or not self.content.get_plugins():
            return None
        first_plugin = self.content.get_plugins()[0]
        plg_instance, plg_cls = first_plugin.get_plugin_instance()
        return plg_instance

    class Meta:
        verbose_name = "blog entries"
        verbose_name_plural = 'blog entries'
        unique_together = (("slug", "creation_date", "blog"),)

    def __unicode__(self):
        return self.title or "<Draft Empty Blog Entry>"
