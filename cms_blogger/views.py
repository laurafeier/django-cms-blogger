from django.http import HttpResponse
from django.shortcuts import get_object_or_404


def entry_page(request, year, month, day, entry_slug):
    return HttpResponse('You blog is missing a layout.')


def landing_page(request, blog_slug):
    return HttpResponse('You blog is missing a layout.')


def bio_page(request, blog_slug, author_slug):
    return HttpResponse('You blog is missing a layout.')
