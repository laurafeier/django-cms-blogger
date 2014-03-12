from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.sites.models import Site
from cms_layouts.layout_response import LayoutResponse
from .models import BlogEntry


def entry_page(request, year, month, day, entry_slug):
    entry = get_object_or_404(
        BlogEntry, creation_date__year=year, creation_date__month=month,
        creation_date__day=day, slug=entry_slug,
        blog__site=Site.objects.get_current())
    layout_response = LayoutResponse(entry, entry.get_layout(), request)
    return layout_response.make_response()


def landing_page(request, blog_slug):
    return HttpResponse('Blog River Missing')


def bio_page(request, blog_slug, author_slug):
    return HttpResponse('Text Plugin missing')
