from django.contrib.syndication.views import Feed
from django.template.context import RequestContext
from .views import get_blog
import urlparse


class BlogFeed(Feed):

    def __init__(self, *args, **kwargs):
        super(BlogFeed, self).__init__(*args, **kwargs)
        self.original_url = ''

    def get_object(self, request, blog_slug):
        obj = get_blog(blog_slug)

        scheme, netloc = urlparse.urlparse(
            request.META.get("HTTP_X_ORIGINAL_URL", ""))[:2]
        prefix = RequestContext(request).get('PROXY_REWRITE_RULE', '')
        self.original_url = urlparse.urlunparse(
            (scheme, netloc, prefix, '', '', '')) if netloc else ''
        return obj

    def title(self, obj):
        return obj.title

    def link(self, obj):
        return self.original_url + obj.get_absolute_url()

    def description(self, obj):
        return obj.tagline

    def items(self, obj):
        return obj.get_entries()[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.short_description

    def item_link(self, item):
        return self.original_url + item.get_absolute_url()

    def item_pubdate(self, item):
        return item.publication_date

    def item_author_name(self, item):
        return item.authors_display_name

    def item_author_email(self, item):
        authors_users = item.authors.filter(user__isnull=False)
        return ", ".join((author.user.email for author in authors_users))

    def item_categories(self, item):
        return item.categories.values_list('name', flat=True)

    def item_enclosure_url(self, item):
        return item.poster_image.url if item.poster_image else ''

    def item_enclosure_mime_type(self, item):
        if not item.poster_image:
            return ''
        return 'image/png'

    def item_enclosure_length(self, item):
        """
        Try to obtain the size of the enclosure
        if the enclosure is present on the FS,
        otherwise returns an hardcoded value.
        """
        if item.poster_image:
            return str(item.poster_image.size)
        return '0'

