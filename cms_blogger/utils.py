from django.utils.encoding import smart_unicode
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.files.base import ContentFile
from .settings import POSTER_IMAGE_WIDTH, POSTER_IMAGE_ASPECT_RATIO
from PIL import Image as PILImage
import StringIO
import os


POSTER_IMAGE_HEIGHT = int(round(
    POSTER_IMAGE_WIDTH / POSTER_IMAGE_ASPECT_RATIO))


def user_display_name(user):
    if user.first_name and user.last_name:
        return u'%s %s' % (user.first_name, user.last_name)
    elif user.email:
        return user.email
    else:
        return smart_unicode(user)


def paginate_queryset(queryset, page, max_per_page):
    paginator = Paginator(queryset, max_per_page)
    try:
        paginated_items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        paginated_items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        paginated_items = paginator.page(paginator.num_pages)
    return paginated_items


def resize_image(file_like_object):
    """
    Resizes an image file based on the with and aspect ration settings and
    returns a django like image that is used to be passed to an file field.
    """

    def _to_django_file(pil_image, filename):
        thumb_io = StringIO.StringIO()
        setattr(thumb_io, 'name', filename)
        pil_image.save(thumb_io)
        dj_file = ContentFile(thumb_io.getvalue(), name=filename)
        if not file_like_object.closed:
            file_like_object.close()
        return dj_file

    full_file_name = file_like_object.name
    filename, _ = os.path.splitext(os.path.basename(full_file_name))
    file_like_object.seek(0)
    try:
        pil_img = PILImage.open(file_like_object)
    except Exception, e:
        raise Exception('Cannot open image %s. Error occured: %s' % (
            full_file_name, e))

    pil_img.load()  # make sure PIL has read the data

    # prepare sizes
    img_width, img_height = pil_img.size
    fixed_width, fixed_height = POSTER_IMAGE_WIDTH, POSTER_IMAGE_HEIGHT
    fixed_size = (fixed_width, fixed_height)

    # make it smaller if too large, preserving its aspect ratio
    if (img_width > fixed_width or img_height > fixed_height):
        pil_img.thumbnail(fixed_size, PILImage.ANTIALIAS)

    # add transparent background
    color = (255, 255, 255, 0)
    background_img = PILImage.new('RGBA', fixed_size, color)
    # refetch size since it could be different than the original
    img_width, img_height = pil_img.size

    # paste image in the center of the transparent image
    start_at_x = (fixed_width - img_width) / 2
    start_at_y = (fixed_height - img_height) / 2
    background_img.paste(pil_img, (start_at_x, start_at_y))

    return _to_django_file(
        background_img, ''.join((filename, os.path.extsep, 'png')))
