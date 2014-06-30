from django.contrib.syndication.views import Feed
from django.template.context import RequestContext
from .views import get_blog_or_404
from .settings import POSTS_ON_RSS
import urlparse


class BlogFeed(Feed):

    def __init__(self, *args, **kwargs):
        super(BlogFeed, self).__init__(*args, **kwargs)
        self.original_url = ''

    def _set_original_url(self, request):
        self.original_url = ''
        scheme, netloc = urlparse.urlparse(
            request.META.get("HTTP_X_ORIGINAL_URL", ""))[:2]
        if netloc:
            context = RequestContext(request)
            proxy_prefix = context.get('PROXY_REWRITE_RULE', '')
            self.original_url = urlparse.urlunparse(
                (scheme, netloc, proxy_prefix, '', '', ''))

    def get_object(self, request, blog_slug):
        obj = get_blog_or_404(blog_slug)
        self._set_original_url(request)
        return obj

    def title(self, obj):
        return obj.title

    def link(self, obj):
        return self.original_url + obj.get_absolute_url()

    def description(self, obj):
        return obj.tagline

    def items(self, obj):
        return obj.get_entries()[:POSTS_ON_RSS]

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

    item_enclosure_mime_type = 'image/png'

    def item_enclosure_length(self, item):
        if item.poster_image:
            return str(item.poster_image.size)
        return '0'

