from django.contrib.admin.views.main import ChangeList
from django.contrib.sites.models import Site
from filer.utils.loader import load_object
from django.conf import settings
from .settings import ALLOWED_SITES_FOR_USER


class BlogChangeList(ChangeList):
    """
    Follows the CMSChangeList logic for setting the current working site.
    """
    site_lookup = 'site__exact'

    def __init__(self, request, model, *args, **kwargs):
        # set site choices for the site chooser widget
        self.set_sites(request, model)
        self.has_access_to_multiple_sites = len(self.sites) > 1

        self.user_session = request.session
        self.current_site = self.get_current_site(request)
        super(BlogChangeList, self).__init__(request, model, *args, **kwargs)

    def set_sites(self, request, model):
        if ALLOWED_SITES_FOR_USER:
            get_sites_for = load_object(ALLOWED_SITES_FOR_USER)
            self.sites = get_sites_for(request.user, model)
        elif settings.CMS_PERMISSION:
            from cms.utils.permissions import get_user_sites_queryset
            self.sites = get_user_sites_queryset(request.user)
        else:
            self.sites = Site.objects.all()

    def get_current_site(self, request):
        if self.site_lookup in request.REQUEST:
            site_pk = request.REQUEST[self.site_lookup]
        else:
            site_pk = request.session.get('cms_admin_site', None)

        if site_pk:
            try:
                return self.sites.get(pk=site_pk)
            except Site.DoesNotExist:
                pass

        return Site.objects.get_current()

    def get_query_set(self, request):
        qs = super(BlogChangeList, self).get_query_set(request)
        return qs.filter(**{self.site_lookup: self.current_site})

    @property
    def current_site(self):
        return self._current_site

    @current_site.setter
    def current_site(self, value):
        self._current_site = value
        self.user_session['cms_admin_site'] = self._current_site.pk


class BlogEntryChangeList(BlogChangeList):
    site_lookup = 'blog__site__exact'
