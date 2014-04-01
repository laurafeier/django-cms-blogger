from django.core.files.storage import get_storage_class
from django.conf import settings
from os import path as os_path
from urlparse import urljoin

BLOGGER_BASE_URL = "blog/"
DEFAULT_BLOGGER_STORAGES = {
    'thumbnail': {
        'ENGINE': 'django.core.files.storage.FileSystemStorage',
        'OPTIONS': {
            'location': os_path.abspath(os_path.join(settings.MEDIA_ROOT, BLOGGER_BASE_URL)),
            'base_url': urljoin(settings.MEDIA_URL, BLOGGER_BASE_URL),
        },
    }
}
BLOGGER_STORAGES = getattr(settings, 'BLOGGER_STORAGES', DEFAULT_BLOGGER_STORAGES)

BLOGGER_THUMBNAIL_STORAGE = get_storage_class(BLOGGER_STORAGES['thumbnail']['ENGINE'])(**BLOGGER_STORAGES['thumbnail']['OPTIONS'])

ALLOWED_SITES_FOR_USER = getattr(
    settings, 'BLOGGER_ALLOWED_SITES_FOR_USER', None)
