from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.http import HttpResponseNotFound
from django.contrib.sites.models import Site
from cms_layouts.layout_response import LayoutResponse
from .models import BlogEntryPage


def entry_page(request, blog_slug, year, month, day, entry_slug):
    entry = get_object_or_404(
        BlogEntryPage, creation_date__year=year, creation_date__month=month,
        creation_date__day=day, slug=entry_slug, blog__slug=blog_slug,
        blog__entries_slugs_with_date=True,
        blog__site=Site.objects.get_current())
    layout = entry.get_layout()
    if not layout:
        return HttpResponseNotFound(
            "<h1>This Entry does not have a layout to render.</h1>")
    layout_response = LayoutResponse(entry, layout, request)
    return layout_response.make_response()


def landing_page(request, blog_slug):
    return HttpResponse('Missing Landing Page content')


def entry_or_bio_page(request, blog_slug, slug):
    try:
        entry = BlogEntryPage.objects.get(
            slug=slug, blog__entries_slugs_with_date=False,
            blog__site=Site.objects.get_current())
    except BlogEntryPage.DoesNotExist:
        return HttpResponse('TODO check for bio page')

    layout = entry.get_layout()
    if not layout:
        return HttpResponseNotFound(
            "<h1>This Entry does not have a layout to render.</h1>")
    layout_response = LayoutResponse(entry, layout, request)
    return layout_response.make_response()
