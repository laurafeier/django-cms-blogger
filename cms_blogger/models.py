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
        _("Insert dates in blog entry URLs"),
        help_text=_(
            'Blogs that are frequently update, especially news-themed blogs,'
            ' often insert dates /2014/03/15/ into their URLs for blog '
            'entries. To insert the date into all blog entries for this blog,'
            ' select ON.\n'))
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


class Blog(AbstractBlog):
    # definitions of the blog model features go here

    # social media integration
    enable_facebook = models.BooleanField(default=True,
        help_text=_('TODO help_text'))
    enable_twitter = models.BooleanField(default=True,
        help_text=_('TODO help_text'))
    # disqus integration
    enable_disqus = models.BooleanField(default=True,
        help_text=_('TODO help_text'))
    disqus_shortname = models.CharField(
        max_length=255, blank=True, null=True,
        help_text=_('TODO help_text'))
    disable_disqus_for_mobile = models.BooleanField(
        _('DISABLE Disqus commenting at mobile breakpoints (<480)'),
        default=False, help_text=_(
            'Select ON to hide comments on phone sized mobile devices.'))

    @property
    def header(self):
        return Placeholder()


class BlogRelatedPage(models.Model):

    uses_layout_type = None
    blog = models.ForeignKey(Blog)

    def get_layout(self):
        return self.blog.get_layout_for(self.uses_layout_type)

    class Meta:
        abstract = True

    @property
    def header(self):
        return self.blog.header

    @property
    def site(self):
        return self.blog.site

    def get_title_obj(self):
        raise NotImplementedError

    def get_absolute_url(self):
        raise NotImplementedError


class ModelWithCMSContent(models.Model):
    """
    Adds a placeholder field for a model.
    It automatically generates an text plugin for the content the first time
        the model gets saved.(This is done through the post_save signal)
    """
    content = PlaceholderField('content')

    def __init__(self, *args, **kwargs):
        super(ModelWithCMSContent, self).__init__(*args, **kwargs)
        self._set_initial_body()

    def _set_initial_body(self):
        if self.pk:
            plugin = self.get_attached_plugin()
            self.body = getattr(plugin, 'body')
        else:
            self.body = 'Sample content'

    def save_body(self):
        plugin = self.get_attached_plugin()
        if plugin.body != self.body:
            plugin.body = self.body
            plugin.save()

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, value):
        self._body = value

    def get_attached_plugin(self):
        if not self.content or not self.content.get_plugins():
            from cms.api import add_plugin
            new_plugin = add_plugin(
                self.content, 'TextPlugin', get_language(), body=self.body)
            return new_plugin
        first_plugin = self.content.get_plugins()[0]
        plg_instance, plg_cls = first_plugin.get_plugin_instance()
        return plg_instance

    class Meta:
        abstract = True


class LandingPage(BlogRelatedPage):

    uses_layout_type = Blog.LANDING_PAGE

    @models.permalink
    def get_absolute_url(self):
        return ('cms_blogger.views.landing_page', (), {
            'blog_slug': self.blog.slug})


class BioPage(BlogRelatedPage):

    uses_layout_type = Blog.BIO_PAGE
    author_name = models.CharField(max_length=255)

    @property
    def content(self):
        #TODO
        return self.blog.content

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

    def __unicode__(self):
        return self.author_name.title()


class BlogEntryPage(BlogRelatedPage, ModelWithCMSContent):

    uses_layout_type = Blog.ENTRY_PAGE

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

    def extra_html_content(self):
        if not self.blog or not self.blog.enable_disqus:
            return ''

        from django.template import Context
        from django.template.loader import get_template
        context = Context({
            'disqus_shortname': self.blog.disqus_shortname,
            'disable_on_mobile': self.blog.disable_disqus_for_mobile
            })
        thread_template = get_template("cms_blogger/disqus_thread.html")
        return thread_template.render(context)

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

    class Meta:
        verbose_name = "blog entries"
        verbose_name_plural = 'blog entries'
        unique_together = (("slug", "blog", "draft_id"),)

    def __unicode__(self):
        return self.title or "<Draft Empty Blog Entry>"


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
        if instance.draft_id and instance.slug and instance.blog_id:
            entry_as_queryset.update(draft_id=None)


@receiver(signals.post_save, sender=BlogEntryPage)
def attach_plugin_to_body(instance, **kwargs):
    instance.save_body()

