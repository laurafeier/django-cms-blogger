from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns('cms_blogger.views',
    url(r'^admin/blogs-select2/', include('django_select2.urls')),
    url(r'blog/(?P<blog_slug>.+)/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d+)/(?P<entry_slug>.+)/$', 'entry_page'),
    url(r'blog/(?P<blog_slug>.+)/(?P<slug>.+)/$', 'entry_or_bio_page'),
    url(r'blog/(?P<blog_slug>.+)/$', 'landing_page'),
)
