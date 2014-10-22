from django.template.defaultfilters import slugify
import re

# from urlify.js
_connection_words = [
    "a", "an", "as", "at", "before", "but", "by", "for", "from",
    "is", "in", "into", "like", "of", "off", "on", "onto", "per",
    "since", "than", "the", "this", "that", "to", "up", "via", "with"];

CONNECTION_WORDS_PATTERN = '\\b(' + '|'.join(_connection_words) + ')\\b'


def urlify(value, keep_connection_words=True):
    title = value[:].strip()
    if not keep_connection_words:
        title = re.sub(CONNECTION_WORDS_PATTERN, '', title)
    return slugify(title).strip('-')


def get_unique_slug(instance, title, queryset, keep_connection_words=True):
    max_length = instance._meta.get_field('slug').max_length

    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    original = urlify(title, keep_connection_words)[:max_length]
    index = 1
    slug_candidate = original
    while queryset.filter(slug=slug_candidate).exists():
        suffix = "-%s" % index
        slug_candidate = original
        if len(suffix) + len(slug_candidate) > max_length:
            slug_candidate = slug_candidate[:max_length - len(suffix)]
        slug_candidate = "%s%s" % (slug_candidate, suffix)
        index += 1

    return slug_candidate
