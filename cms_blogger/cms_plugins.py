from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import ugettext_lazy as _
from django.db import models
from .models import BlogPromotion
from .widgets import ToggleWidget


class BlogPromotionPlugin(CMSPluginBase):
    model = BlogPromotion
    name = _("Blog Promotion Plugin")
    render_template = "cms_blogger/blog_promotion.html"
    formfield_overrides = {
        models.BooleanField: {'widget': ToggleWidget}
    }

    def render(self, context, instance, placeholder):
        plugin = instance
        blog = instance.blog
        context.update({
            'plugin': plugin,
            'blog': blog,
            'hide_blog_title': not instance.blog_title,
            'hide_blog_tagline': not instance.blog_tagline,
            'hide_blog_image': not instance.branding_image,
            'hide_entry_description': not instance.display_abstract,
            'hide_entry_image': not instance.display_thumbnails,
            'entries': blog.get_entries()[:instance.number_of_entries]
        })
        return context

    def get_form(self, request, obj=None, **kwargs):
        formCls = super(BlogPromotionPlugin, self).get_form(
            request, obj, **kwargs)
        plugin_page = getattr(request, 'current_page', None)
        blog_field = formCls.base_fields.get('blog')
        if plugin_page and blog_field:
            blog_field.queryset = blog_field.queryset.filter(
                site=plugin_page.site)
        return formCls

plugin_pool.register_plugin(BlogPromotionPlugin)
