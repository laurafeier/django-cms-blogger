from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.contenttypes.generic import GenericRelation
from django.utils.translation import get_language
from django.template.defaultfilters import slugify
from django.template.loader import get_template
from django.db.models import signals
from django.dispatch import receiver
from django.http import HttpResponseNotFound

from cms.models.fields import PlaceholderField
from cms.models import Placeholder, CMSPlugin

from cms_layouts.models import LayoutTitle, Layout
from cms_layouts.layout_response import LayoutResponse

from filer.fields.image import FilerImageField
import filer

from .settings import POSTER_IMAGE_STORAGE, UPLOAD_TO_PREFIX, BLOGS_URL_PREFIX
from .utils import user_display_name
from .slug import get_unique_slug
from .managers import EntriesManager

import os
import datetime


FILENAME_LENGTH = 100
CATEGORY_NAME_LENGTH = 30
MAX_CATEGORIES_IN_PLUGIN = 20


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
            if plugin is None:
                return
            # get_attached_plugin always fetches the plugin from the db;
            #   the html cleaning cannot be done in the clean method since the
            #   plugin instance from there will be different from this one
            plugin.body = getattr(self, body_attr)
            plugin.clean()
            plugin.clean_plugins()
            plugin.save()

        def delete(self, *args, **kwargs):
            try:
                placeholder_pk = getattr(self, content_attr).pk
            except Placeholder.DoesNotExist:
                pass
            super(ModelWithCMSContent, self).delete(*args, **kwargs)
            try:
                phd = Placeholder.objects.get(pk=placeholder_pk)
                for plg in phd.cmsplugin_set.all():
                    plg.delete()
                phd.delete()
            except Placeholder.DoesNotExist:
                pass

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
                 lambda x, v: setattr(x, "_%s" % body_attr, v)))
    ModelWithCMSContent.add_to_class(plugin_getter, get_attached_plugin)
    return ModelWithCMSContent


def contribute_with_title(cls):
    # required in order to make sure page_attribute templatetag will fetch
    #   these attributes from the title object
    # this decorator requires the definition of get_title_obj method
    #   that will return an instance on LayoutTitle
    valid_title_attributes = [
        "title", "slug", "meta_description", "meta_keywords", "page_title",
        "menu_title"]

    for attr in valid_title_attributes:
        def get_title_obj_attribute(obj, *args, **kwargs):
            return getattr(obj.get_title_obj(), attr, '')

        cls.add_to_class('get_%s' % attr, get_title_obj_attribute)
    return cls


def blog_page(cls):
    # adds a blog foreign key(with a related name if specified) to a model
    # blog foreign key is required by all blog related pages.
    blog = models.ForeignKey(
        Blog, related_name=getattr(cls, 'blog_related_name', None))
    modified_at = models.DateTimeField(auto_now=True, db_index=True)
    cls.add_to_class('blog', blog)
    cls.add_to_class('modified_at', modified_at)
    cls = contribute_with_title(cls)
    return cls


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
        if attached_blog:
            return attached_blog[0]
        attached_home_blog = self.homeblog_set.all()[:1]
        return attached_home_blog[0] if attached_home_blog else None

    def get_absolute_url(self):
        return self.blog.get_absolute_url() if self.blog else ''

    def is_visible(self):
        return self.blog.in_navigation if self.blog else False

    @property
    def menu_id(self):
        if self.blog.is_home:
            return 0
        if not self.id:
            return None
        return self.id * -1


@contribute_with_title
class AbstractBlog(models.Model):
    site_lookup = 'site__exact'
    is_home = False

    title = models.CharField(
        _('title'), max_length=50, blank=False, null=False,
        help_text=_('Blog Title'))
    site = models.ForeignKey(
        Site, help_text=_('Blog Site'), verbose_name=_("site"))
    modified_at = models.DateTimeField(auto_now=True, db_index=True)

    layouts = GenericRelation(Layout)
    # header metadata
    tagline = models.CharField(
        _('tagline'), max_length=70, blank=True, null=True,
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

    class Meta:
        abstract = True

    def get_absolute_url(self):
        raise NotImplementedError

    def get_feed_url(self):
        from django.core.urlresolvers import reverse
        url_kwargs = {}
        if not self.is_home and self.slug:
            url_kwargs = {'blog_slug': self.slug}
        return reverse('blog_feed', args=(), kwargs=url_kwargs)

    def get_layout(self):
        raise NotImplementedError

    def render_header(self, request, context):
        return get_template("cms_blogger/blog_header.html").render(context)

    def render_content(self, request, context):
        # landing page view passes paginated entries and blog to the context
        return get_template("cms_blogger/blog_content.html").render(context)

    def get_entries(self):
        return BlogEntryPage.objects.none()

    @property
    def attached_image(self):
        try:
            return self.branding_image
        except filer.models.Image.DoesNotExist:
            return None

    def get_title_obj(self):
        title = LayoutTitle()
        title.page_title = title.title = self.title
        title.slug = getattr(self, 'slug', '')
        return title

    def save(self, *args, **kwargs):
        try:
            site = self.site
        except Site.DoesNotExist:
            site = None
        self.site = site or Site.objects.get_current()
        super(AbstractBlog, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s - %s" % (self.title, self.site.name)


class HomeBlog(AbstractBlog):
    slug = BLOGS_URL_PREFIX
    is_home = True

    def get_layout(self):
        try:
            return self.layouts.all()[0]
        except IndexError:
            return None

    def get_entries(self):
        ordering = ('-publication_date', 'slug')
        site_entries = BlogEntryPage.objects.on_site(self.site)
        return site_entries.published().order_by(*ordering)

    @models.permalink
    def get_absolute_url(self):
        return ('cms_blogger.views.landing_page', (), {})

    def save(self, *args, **kwargs):
        self.title = self.title or 'Latest blog posts'
        super(HomeBlog, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Super Landing Page"
        verbose_name_plural = "Super Landing Page"


class Blog(AbstractBlog):
    # values that are used distinguish layout types for this blog
    ALL = 0  # layout type that will be used by default by all blog pages
    LANDING_PAGE = 1
    ENTRY_PAGE = 2
    BIO_PAGE = 3

    LAYOUTS_CHOICES = {
        ALL: 'All Blog-related Page Layouts',
        LANDING_PAGE: 'Blog Landing Page',
        ENTRY_PAGE: 'Blog Entry Page',
        # BIO_PAGE: 'Blog Bio Page'
    }

    slug = models.SlugField(
        _("slug"), max_length=50, help_text=_('Blog Slug'))

    entries_slugs_with_date = models.BooleanField(
        _("Dates in blog entry URLs"),
        help_text=_('Blog Entries With Slugs'))
    # permission system
    allowed_users = models.ManyToManyField(User, verbose_name=_("Add Users"))
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

    def get_layout_for(self, layout_type):
        if layout_type not in Blog.LAYOUTS_CHOICES.keys():
            raise NotImplementedError
        try:
            return self.layouts.filter(layout_type__in=[
                layout_type, Blog.ALL]).order_by('-layout_type')[0]
        except IndexError:
            return None

    def get_entries(self):
        ordering = ('-publication_date', 'slug')
        return self.blogentrypage_set.published().order_by(*ordering)

    @models.permalink
    def get_absolute_url(self):
        return ('cms_blogger.views.landing_page', (), {
            'blog_slug': self.slug})

    def get_layout(self):
        return self.get_layout_for(Blog.LANDING_PAGE)

    class Meta:
        unique_together = (("slug", "site"),)


class BlogRelatedPage(object):
    # any blog related pages needs to have a layout, a content and a header
    #   that can be rendered by the layout
    uses_layout_type = None
    site_lookup = 'blog__site__exact'

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


class Author(models.Model):

    name = models.CharField(_('name'), max_length=150)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='blog_authors')
    slug = models.SlugField(
        _('slug'), max_length=150,
        help_text=_("Used to build the author's URL."))

    def save(self, *args, **kwargs):
        if not self.slug and self.display_name:
            unique_qs = Author.objects.all()
            self.slug = get_unique_slug(self, self.display_name, unique_qs)
        super(Author, self).save(*args, **kwargs)

    @property
    def display_name(self):
        return self.name or user_display_name(self.user)

    def __unicode__(self):
        return self.display_name


@blog_page
class BioPage(models.Model, BlogRelatedPage):

    uses_layout_type = Blog.BIO_PAGE
    author = models.ForeignKey(Author)

    @property
    def slug(self):
        return self.author.slug

    @models.permalink
    def get_absolute_url(self):
        return ('cms_blogger.views.entry_or_bio_page', (), {
            'blog_slug': self.blog.slug,
            'slug': self.slug})

    def get_title_obj(self):
        title = LayoutTitle()
        title.page_title = self.author.display_name.title()
        title.slug = self.slug
        return title

    def __unicode__(self):
        return self.author.display_name.title()


def upload_entry_image(instance, filename):
    base, ext = os.path.splitext(filename)
    new_base = '%s%s%s_%s' % (
        UPLOAD_TO_PREFIX,
        os.sep,
        datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f"),
        slugify(base),)

    new_ext = ext[:1] + ext[1:].lower()
    new_base_trimmed = new_base[:(FILENAME_LENGTH - len(new_ext))]

    return new_base_trimmed + new_ext


@blog_page
class BlogEntryPage(getCMSContentModel(content_attr='content'),
                    BlogRelatedPage):
    uses_layout_type = Blog.ENTRY_PAGE
    title = models.CharField(_('title'), max_length=255)
    slug = models.SlugField(
        _('slug'), max_length=255,
        help_text=_("Used to build the entry's URL."))
    publication_date = models.DateTimeField(
        _('publication date'),
        db_index=True, default=timezone.now,
        help_text=_("Used to build the entry's URL."))

    poster_image = models.ImageField(
        _("Thumbnail Image"), upload_to=upload_entry_image, blank=True,
        storage=POSTER_IMAGE_STORAGE)
    caption = models.CharField(
        _('caption'), max_length=70, blank=True, null=True)
    credit = models.CharField(
        _('credit'), max_length=35, blank=True, null=True)

    authors = models.ManyToManyField(
        Author, verbose_name=_('Blog Entry Authors'),
        related_name='blog_entries')

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
    enable_poster_image = models.BooleanField(
        _('Display thumbnail'), default=True,
        help_text=_('Display thumbnail in blog entry'))

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
    def authors_display_name(self):
        return ", ".join(('%s' % author
                          for author in self.authors.all()))

    def extra_html_before_content(self, request, context):
        if not self.blog:
            return ''
        # wrap the whole blog post html into a box; box closed
        #   in extra_html_after_content
        start_tag = '<div class="blog-post clearfix box">'
        template = get_template("cms_blogger/entry_top.html")
        return "%s%s" % (start_tag, template.render(context))

    def extra_html_after_content(self, request, context):
        if not self.blog:
            return ''
        # close the box opened in the extra_html_before_content
        end_tag = '</div>'
        template = get_template("cms_blogger/entry_bottom.html")
        return "%s%s" % (template.render(context), end_tag)

    def get_title_obj(self):
        title = LayoutTitle()
        title.title = self.title
        title.page_title = self.seo_title
        title.slug = self.slug
        title.meta_description = self.short_description
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
                'entry_slug': self.slug}
            )
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
        context.update({'entry': self, 'blog': self.blog, })
        return LayoutResponse(
            self, layout, request, context=context).make_response()

    def previous_post(self):
        if not self.blog:
            return None
        query_for_prev = Q(
            Q(Q(publication_date=self.publication_date) &
              Q(slug__lt=self.slug)) |
            Q(publication_date__lt=self.publication_date))
        ordering = ('-publication_date', '-slug')
        siblings = self.blog.get_entries().exclude(id=self.id)
        prev_post = siblings.filter(query_for_prev).order_by(*ordering)[:1]
        return prev_post[0] if prev_post else None

    def next_post(self):
        if not self.blog:
            return None
        query_for_next = Q(
            Q(Q(publication_date=self.publication_date) &
              Q(slug__gt=self.slug)) |
            Q(publication_date__gt=self.publication_date))
        ordering = ('publication_date', 'slug')
        siblings = self.blog.get_entries().exclude(id=self.id)
        next_post = siblings.filter(query_for_next).order_by(*ordering)[:1]
        return next_post[0] if next_post else None

    def delete(self, *args, **kwargs):
        path = self.poster_image.name
        super(BlogEntryPage, self).delete(*args, **kwargs)
        if path:
            self.poster_image.storage.delete(path)

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            unique_qs = BlogEntryPage.objects.filter(
                blog=self.blog_id, draft_id=None)
            self.slug = get_unique_slug(self, self.title, unique_qs)
        super(BlogEntryPage, self).save(*args, **kwargs)
        # _old_poster_image attribute is available only when a new image
        #   was uploaded for the poster image field. This attribute holds the
        #   full file name for the file that's going to be replaced.
        if getattr(self, '_old_poster_image', ''):
            self.poster_image.storage.delete(self._old_poster_image)

    class Meta:
        verbose_name = "blog entry"
        verbose_name_plural = 'blog entries'
        unique_together = (("slug", "blog", "draft_id"),)

    def __unicode__(self):
        return "<Draft Empty Blog Entry>" if self.is_draft else self.title


@blog_page
class BlogCategory(models.Model, BlogRelatedPage):
    blog_related_name = 'categories'
    name = models.CharField(
        _('name'), max_length=CATEGORY_NAME_LENGTH, db_index=True)
    slug = models.SlugField(_('slug'), max_length=30)
    entries = models.ManyToManyField(
        BlogEntryPage, related_name='categories')

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
        return self.entries.published().filter(
            blog=self.blog).order_by('-publication_date', 'slug').distinct()

    def get_layout(self):
        return self.blog.get_layout_for(Blog.LANDING_PAGE)

    def save(self, *args, **kwargs):
        if not self.slug and self.name and self.blog:
            unique_qs = BlogCategory.objects.filter(blog=self.blog)
            self.slug = get_unique_slug(
                self, self.name, unique_qs, keep_connection_words=False)
        super(BlogCategory, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = (("slug", 'blog'),)


class RiverPlugin(CMSPlugin):

    title = models.CharField(_('title'), max_length=100)
    # allow maximum 20 categories and compute max chars taking commas into
    #   consideration
    categories = models.CharField(
        BlogCategory, max_length=(
            CATEGORY_NAME_LENGTH * MAX_CATEGORIES_IN_PLUGIN +
            MAX_CATEGORIES_IN_PLUGIN - 1))
    display_abstract = models.BooleanField(default=True)
    display_thumbnails = models.BooleanField(default=True)
    paginate_entries = models.BooleanField(default=True)
    number_of_entries = models.PositiveIntegerField(
        _('Entries to Display'), default=10)

    def get_entries(self):
        qs = BlogEntryPage.objects.published().filter(
            categories__name__in=self.categories.split(','),
            blog__site=Site.objects.get_current()
        ).distinct().order_by('-publication_date', 'slug')
        return qs

    def __unicode__(self):
        return self.title


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


@receiver(signals.pre_delete, sender=User)
def fetch_author_to_update_name_for(instance, **kwargs):
    author = None
    try:
        author = Author.objects.get(user=instance)
    except Author.DoesNotExist:
        pass
    except Author.MultipleObjectsReturned:
        authors = Author.objects.filter(user=instance).order_by(slug)
        author = authors[0]
        for to_merge_author in author[1:]:
            author.blog_entries.add(*to_merge_author.entries.all())
    except Exception:
        raise
    finally:
        if author:
            setattr(instance, '_author_to_update', author.pk)


@receiver(signals.post_delete, sender=User)
def update_author_name(instance, **kwargs):
    if hasattr(instance, '_author_to_update'):
        try:
            author_pk = getattr(instance, '_author_to_update')
            author = Author.objects.get(id=author_pk)
            author.name = user_display_name(instance)
            author.save()
        except:
            pass


@receiver(signals.pre_save, sender=BlogCategory)
def category_update(instance, **kwargs):
    current_time = timezone.now()
    instance.blog.modified_at = current_time
    instance.blog.save()


@receiver(signals.pre_save, sender=BlogEntryPage)
def entry_update(instance, **kwargs):
    current_time = timezone.now()
    instance.blog.modified_at = current_time
    instance.blog.save()


@receiver(signals.pre_delete, sender=BlogCategory)
def category_update(instance, **kwargs):
    current_time = timezone.now()
    instance.blog.modified_at = current_time
    instance.blog.save()


@receiver(signals.pre_delete, sender=BlogEntryPage)
def entry_update(instance, **kwargs):
    current_time = timezone.now()
    instance.blog.modified_at = current_time
    instance.blog.save()
