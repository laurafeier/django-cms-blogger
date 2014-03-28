from django.contrib.admin.views.main import ChangeList
from django.contrib.sites.models import Site
from cms.utils.permissions import get_user_sites_queryset
from django.conf import settings


class BlogChangeList(ChangeList):
    """
    Follows the CMSChangeList logic for setting the current working site.
    """
    site_lookup = 'site__exact'

    def __init__(self, request, *args, **kwargs):
        self._current_site = self.get_current_site(request)
        super(BlogChangeList, self).__init__(request, *args, **kwargs)
        if self._current_site:
            request.session['cms_admin_site'] = self._current_site.pk

        # set site choices for the site chooser widget
        if settings.CMS_PERMISSION:
            self.sites = get_user_sites_queryset(request.user)
        else:
            self.sites = Site.objects.all()
        self.has_access_to_multiple_sites = len(self.sites) > 1

    def get_current_site(self, request):
        # similar with cms.utils.plugins.current_site but it accepts
        #   other site lookups
        if self.site_lookup in request.REQUEST:
            return Site.objects.get(pk=request.REQUEST[self.site_lookup])
        else:
            site_pk = request.session.get('cms_admin_site', None)
            if site_pk:
                try:
                    return Site.objects.get(pk=site_pk)
                except Site.DoesNotExist:
                    return None
            else:
                return Site.objects.get_current()

    def get_query_set(self, request):
        qs = super(BlogChangeList, self).get_query_set(request)
        return qs.filter(**{self.site_lookup: self._current_site})

    def current_site(self):
        return self._current_site


class BlogEntryChangeList(BlogChangeList):
    site_lookup = 'blog__site__exact'
