from django.contrib.sites.models import Site


def get_allowed_sites(user, model):
    """
    For testing purposes regular users can only see blogs for site example.com
    """
    if user.is_superuser:
        return Site.objects.all()
    return Site.objects.filter(id=1)
