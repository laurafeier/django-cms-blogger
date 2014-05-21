# -*- coding: utf-8 -*-
from django.contrib.sitemaps import Sitemap
from django.contrib.sites.models import Site
from django.core import paginator
from django.db.models import Q
from cms_blogger.models import (
    BlogEntryPage,
    BlogCategory,
    BioPage,
    Blog,
)
import itertools
import datetime


class BloggerSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        # Blogs, BlogRelatedPages, BlogEntryPages
        current_site = Site.objects.get_current()
        blog_current_site = Q(blog__site=current_site)
        blogs = Blog.objects.filter(site=current_site)
        # bio_pages = BioPage.objects.filter(blog_current_site)
        entry_pages = BlogEntryPage.objects.published().filter(blog_current_site)
        blog_categories = BlogCategory.objects.filter(blog_current_site)
        chained = itertools.chain(
            blogs,
            # bio_pages,
            entry_pages,
            blog_categories,
        )
        return list(chained)

    def lastmod(self, blog_related_object):
        latest = blog_related_object.modified_at
        return latest
