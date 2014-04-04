from django.core.files.storage import get_storage_class
from django.conf import settings
from os import path as os_path
from urlparse import urljoin
from filer.settings import FILER_PUBLICMEDIA_STORAGE


UPLOAD_TO_PREFIX = getattr(settings, 'BLOGGER_UPLOAD_TO_PREFIX', "blog")

USE_FILER_STORAGE = getattr(settings, 'BLOGGER_USE_FILER_STORAGE', False) 


#get_storage_class(BLOGGER_STORAGES['thumbnail']['ENGINE'])(**BLOGGER_STORAGES['thumbnail']['OPTIONS'])

ALLOWED_SITES_FOR_USER = getattr(
    settings, 'BLOGGER_ALLOWED_SITES_FOR_USER', None)