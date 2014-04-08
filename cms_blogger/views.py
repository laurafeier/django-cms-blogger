from django.http import HttpResponse, Http404, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.contrib.sites.models import Site
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from cms_layouts.layout_response import LayoutResponse
from .models import BlogEntryPage, Blog
from .settings import POSTS_ON_LANDING_PAGE


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
    return entry.render_to_response(request)


def landing_page(request, blog_slug):
    blog = get_object_or_404(
        Blog, slug=blog_slug, site=Site.objects.get_current())
    layout = blog.get_layout()
    if not layout:
        return HttpResponseNotFound(
            "<h1>This Blog Landing Page does not have a "
            "layout to render.</h1>")

    paginator = Paginator(blog.get_entries(), POSTS_ON_LANDING_PAGE)
    page = request.GET.get('page')
    try:
        entries = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        entries = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        entries = paginator.page(paginator.num_pages)
    blog.paginated_entries = entries
    return LayoutResponse(blog, layout, request).make_response()


def entry_or_bio_page(request, blog_slug, slug):
    entry_qs = get_entries_queryset_for_request(request)
    try:
        entry = entry_qs.get(
            slug=slug, blog__slug=blog_slug,
            blog__entries_slugs_with_date=False)
    except BlogEntryPage.DoesNotExist:
        raise Http404
    return entry.render_to_response(request)
