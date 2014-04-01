from django.conf import settings

ALLOWED_SITES_FOR_USER = getattr(
    settings, 'BLOGGER_ALLOWED_SITES_FOR_USER', None)
