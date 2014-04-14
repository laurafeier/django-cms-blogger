from django import template

register = template.Library()

def paginator(context, page, adjacent_pages=2):
    """
    Based on the logic provided here: https://djangosnippets.org/snippets/73/
    """
    page_no = page.number
    total_pages = page.paginator.num_pages
    page_numbers = filter(
        lambda n: n > 0 and n <= total_pages,
        range(page_no - adjacent_pages, page_no + adjacent_pages + 1))
    show_first = 1 not in page_numbers
    is_after_first = page_numbers[0] - 1 == 1
    show_last = total_pages not in page_numbers
    is_before_last = page_numbers[len(page_numbers) - 1] + 1 == total_pages
    return {
        'page': page,
        'page_numbers': page_numbers,
        'show_first': show_first,
        'show_first_ellipsis': show_first and not is_after_first,
        'show_last': show_last,
        'show_last_ellipsis': show_last and not is_before_last,
        'extra_params': context.get('extra_params')
    }

register.inclusion_tag('cms_blogger/paginator.html', takes_context=True)(paginator)
