from django.utils.encoding import smart_unicode
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


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
