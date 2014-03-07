from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('cms_blogger.views',
    url(r'blog/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d+)/(?P<entry_slug>.+)/$', 'entry_page'),
    url(r'blog/(?P<blog_slug>.+)/(?P<author_slug>.+)/$', 'bio_page'),
    url(r'blog/(?P<blog_slug>.+)/$', 'landing_page'),
)
