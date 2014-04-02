from django.http import HttpResponse, Http404, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.contrib.sites.models import Site
from cms_layouts.layout_response import LayoutResponse
from .models import BlogEntryPage, Blog


def get_entries_queryset_for_request(request):
    preview = 'preview' in request.GET and request.user.is_staff
    entry_qs = BlogEntryPage.objects.on_site()
    if not preview:
        entry_qs = entry_qs.published()
    return entry_qs


def entry_page(request, blog_slug, year, month, day, entry_slug):
    entry_qs = get_entries_queryset_for_request(request)
    try:
        entry = entry_qs.get(
            publication_date__year=year,
            publication_date__month=month,
            publication_date__day=day,
            slug=entry_slug, blog__slug=blog_slug,
            blog__entries_slugs_with_date=True)
    except BlogEntryPage.DoesNotExist:
        raise Http404
    layout = entry.get_layout()
    if not layout:
        return HttpResponseNotFound(
            "<h1>This Entry does not have a layout to render.</h1>")
    return LayoutResponse(entry, layout, request).make_response()


def landing_page(request, blog_slug):
    blog = get_object_or_404(
        Blog, slug=blog_slug, site=Site.objects.get_current())
    layout = blog.get_layout()
    if not layout:
        return HttpResponseNotFound(
            "<h1>This Blog Landing Page does not have a "
            "layout to render.</h1>")
    return LayoutResponse(blog, layout, request).make_response()


def entry_or_bio_page(request, blog_slug, slug):
    entry_qs = get_entries_queryset_for_request(request)
    try:
        entry = entry_qs.get(
            slug=slug, blog__slug=blog_slug,
            blog__entries_slugs_with_date=False)
    except BlogEntryPage.DoesNotExist:
        raise Http404
    layout = entry.get_layout()
    if not layout:
        return HttpResponseNotFound(
            "<h1>This Entry does not have a layout to render.</h1>")
    return LayoutResponse(entry, layout, request).make_response()
