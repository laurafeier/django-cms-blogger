from django.contrib.admin.views.main import ChangeList
from .utils import get_current_site, get_allowed_sites


class BlogChangeList(ChangeList):
    """
    Follows the CMSChangeList logic for setting the current working site.
    """

    def __init__(self, request, model, *args, **kwargs):
        # set site choices for the site chooser widget
        self.sites = get_allowed_sites(request, model)
        self.has_access_to_multiple_sites = len(self.sites) > 1
        self.site_lookup = model.site_lookup
        self.current_site = get_current_site(request, model)
        super(BlogChangeList, self).__init__(request, model, *args, **kwargs)

    def get_query_set(self, request):
        qs = super(BlogChangeList, self).get_query_set(request)
        return qs.filter(**{self.site_lookup: self.current_site})

    def get_results(self, request):
        self.root_query_set = self.root_query_set.filter(
            **{self.site_lookup: self.current_site})
        super(BlogChangeList, self).get_results(request)


class BlogEntryChangeList(BlogChangeList):
    pass
