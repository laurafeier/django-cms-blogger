from django.conf.urls.defaults import patterns, url, include
from cms_blogger import feeds, settings


blogger_patterns = patterns(
    'cms_blogger.views',
    url(r'/(?P<blog_slug>.+)/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d+)/(?P<entry_slug>.+)/$', 'entry_page'),
    url(r'/(?P<blog_slug>.+)/category/(?P<slug>.+)/$', 'category_page'),
    url(r'(?:/(?P<blog_slug>.+))?/rss/$', feeds.BlogFeed()),
    url(r'/(?P<blog_slug>.+)/(?P<slug>.+)/$', 'entry_or_bio_page'),
    url(r'(?:/(?P<blog_slug>.+))?/$', 'landing_page')
)

urlpatterns = patterns(
    '',
    url(r'^admin/blogs-select2/', include('django_select2.urls')),
    url(r'^' + settings.BLOGS_URL_PREFIX, include(blogger_patterns)),
)
