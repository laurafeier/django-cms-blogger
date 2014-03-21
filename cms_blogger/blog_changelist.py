from django.contrib.admin.views.main import ChangeList
from cms.utils.permissions import get_user_sites_queryset
from django.conf import settings


class BlogChangeList(ChangeList):
    """
    Follows the CMSChangeList logic for setting the current working site.
    """

    def __init__(self, request, *args, **kwargs):
        from cms.utils.plugins import current_site
        self._current_site = current_site(request)
        super(BlogChangeList, self).__init__(request, *args, **kwargs)
        if self._current_site:
            request.session['cms_admin_site'] = self._current_site.pk

        # set site choices for the site chooser widget
        if settings.CMS_PERMISSION:
            self.sites = get_user_sites_queryset(request.user)
        else:
            self.sites = Site.objects.all()
        self.has_access_to_multiple_sites = len(self.sites) > 1

    def get_query_set(self, request):
        qs = super(BlogChangeList, self).get_query_set(request)
        return qs.filter(site=self._current_site)

    def current_site(self):
        return self._current_site
