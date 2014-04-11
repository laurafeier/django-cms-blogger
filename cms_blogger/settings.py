from django.conf import settings

POSTS_ON_LANDING_PAGE = getattr(
    settings, 'BLOGGER_POSTS_ON_LANDING_PAGE', 2)
ALLOWED_SITES_FOR_USER = getattr(
    settings, 'BLOGGER_ALLOWED_SITES_FOR_USER', None)
