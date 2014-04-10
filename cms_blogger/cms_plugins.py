from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import ugettext_lazy as _

from .models import BlogPromotion


class BlogPromotionPlugin(CMSPluginBase):
    model = BlogPromotion
    name = _("Blog Promotion Plugin")
    render_template = "cms_blogger/blog_promotion.html"

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


plugin_pool.register_plugin(BlogPromotionPlugin)
