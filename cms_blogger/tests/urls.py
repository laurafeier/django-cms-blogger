from django.conf.urls import patterns, include, url
from django.contrib.sitemaps.views import sitemap
from cms_blogger.sitemaps import BloggerSitemap

from django.contrib import admin
admin.autodiscover()


sitemap_params = {
    'sitemaps': {
        'cmsblogger': BloggerSitemap,
    }
}

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('cms_blogger.urls')),
    url(r'^', include('cms.urls')),
    url(r'^sitemap.xml$', sitemap, sitemap_params, name='blogger-sitemap'),
)
