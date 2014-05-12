from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import ugettext_lazy as _
from django.db import models

from .models import RiverPlugin
from .widgets import ToggleWidget
from .forms import BlogRiverForm
from .admin_helper import AdminHelper
from .utils import paginate_queryset


class BlogRiverPlugin(AdminHelper, CMSPluginBase):
    model = RiverPlugin
    name = _("Blog River Plugin")
    render_template = "cms_blogger/blog_promotion.html"
    form = BlogRiverForm
    change_form_template = "admin/cms_blogger/promotion_plugin_form.html"
    formfield_overrides = {
        models.BooleanField: {'widget': ToggleWidget}
    }

    def render(self, context, instance, placeholder):
        request = context['request']
        entries = paginate_queryset(
            instance.get_entries(), request.GET.get('blog_promo_page'),
            instance.number_of_entries)
        context.update({
            'plugin': instance,
            'entries': entries,
            'hide_entry_description': not instance.display_abstract,
            'hide_entry_image': not instance.display_thumbnails,
            'paginate_entries': instance.paginate_entries,
            'page_param_name': 'blog_promo_page'
        })
        return context

    def render_change_form(self, request, context, *args, **kwargs):
        res = super(BlogRiverPlugin, self).render_change_form(
            request, context, *args, **kwargs)
        if 'media' in context:
            context['media'] = self._upgrade_jquery(context['media'])
        return res


plugin_pool.register_plugin(BlogRiverPlugin)
