from django.core.files.storage import get_storage_class
from django.conf import settings
from os import path as os_path
from urlparse import urljoin
from filer.settings import FILER_PUBLICMEDIA_STORAGE


UPLOAD_TO_PREFIX = getattr(settings, 'BLOGGER_UPLOAD_TO_PREFIX', "blog")

USE_FILER_STORAGE = getattr(settings, 'BLOGGER_USE_FILER_STORAGE', False)

#for poster_image
FILENAME_LENGTH = getattr(settings, 'BLOGGER_FILENAME_LENGTH', 100)

ALLOWED_THUMBNAIL_IMAGE_TYPES = getattr(settings, 'BLOGGER_ALLOWED_THUMBNAIL_IMAGE_TYPES', ['jpg', 'jpeg', 'png', 'gif'])

MAXIMUM_THUMBNAIL_FILE_SIZE = getattr(settings, 'BLOGGER_MAXIMUM_THUMBNAIL_FILE_SIZE', 200*1024*1024) #bytes

MINIMUM_POSTER_IMAGE_WIDTH = getattr(settings, 'BLOGGER_MINIMUM_POSTER_IMAGE_WIDTH', 640)
POSTER_IMAGE_ASPECT_RATIO = getattr(settings, 'BLOGGER_POSTER_IMAGE_ASPECT_RATIO', 16.0/9.0)
POSTER_IMAGE_ASPECT_RATIO_ERROR = getattr(settings, 'BLOGGER_POSTER_IMAGE_ASPECT_RATIO_ERROR', 0.01)

#get_storage_class(BLOGGER_STORAGES['thumbnail']['ENGINE'])(**BLOGGER_STORAGES['thumbnail']['OPTIONS'])

POSTS_ON_LANDING_PAGE = getattr(
    settings, 'BLOGGER_POSTS_ON_LANDING_PAGE', 25)
ALLOWED_SITES_FOR_USER = getattr(
    settings, 'BLOGGER_ALLOWED_SITES_FOR_USER', None)
