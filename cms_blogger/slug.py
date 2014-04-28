from django.template.defaultfilters import slugify


def get_unique_slug(instance, title, queryset):
    max_length = instance._meta.get_field('slug').max_length

    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    def _slugify(value):
        return slugify(value.strip()).strip('-')[:max_length]

    original = _slugify(title)
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
