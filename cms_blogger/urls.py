from django.conf.urls.defaults import patterns, url, include
from cms_blogger import settings


def blogger_url(patt, view):
    return url(r'^' + settings.BLOGS_URL_PREFIX + patt, view)


urlpatterns = patterns(
    'cms_blogger.views',
    url(r'^admin/blogs-select2/', include('django_select2.urls')),
    blogger_url(r'/(?P<blog_slug>.+)/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d+)/(?P<entry_slug>.+)/$', 'entry_page'),
    blogger_url(r'/(?P<blog_slug>.+)/category/(?P<slug>.+)/$', 'category_page'),
    blogger_url(r'/(?P<blog_slug>.+)/(?P<slug>.+)/$', 'entry_or_bio_page'),
    blogger_url(r'(?:/(?P<blog_slug>.+))?/$', 'landing_page'),
)
