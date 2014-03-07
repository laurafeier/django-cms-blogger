from django import forms
from django.core.exceptions import ValidationError
from cms_layouts.models import Layout
from .models import Blog


class LayoutForm(forms.ModelForm):
    # layout_type = forms.ChoiceField(
    #     label='Layout Type', choices=Blog.LAYOUTS_CHOICES.items())

    class Meta:
        model = Layout
        # fields = ('from_page', )


class BlogForm(forms.ModelForm):

    class Meta:
        model = Blog

    def clean_slug(self):
        return self.cleaned_data.get('slug', '').lower()

    def clean_site(self):
        site = self.cleaned_data.get('site')
        if not site:
            return site
        from cms.models import Page
        try:
            cms_home_page = Page.objects.get_home(site)
        except Exception as e:
            raise ValidationError("%s" % e)
        return site
