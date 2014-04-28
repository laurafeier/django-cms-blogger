from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.sites.models import Site
from django.contrib.admin.util import flatten_fieldsets
from django.core.urlresolvers import reverse

from cms_blogger.models import *
from cms_blogger import admin, forms
from cms.api import create_page, add_plugin

from cms_layouts.models import Layout
from cms_layouts.slot_finder import get_fixed_section_slots


class TestBlogModel(TestCase):

    def setUp(self):
        superuser = User.objects.create_superuser(
            'admin', 'admin@cms_blogger.com', 'secret')
        self.client.login(username='admin', password='secret')
        self.user = superuser

    def test_creation(self):
        # only title and slug are required fields
        data = {'title': 'one title', 'slug': 'one-title'}
        blog = Blog.objects.create(**data)
        # blog site should be prepopulated with the current site
        self.assertEquals(blog.site.pk, 1)
        landing_url = reverse('cms_blogger.views.landing_page', kwargs={
            'blog_slug': 'one-title'})
        self.assertEquals(blog.get_absolute_url(), landing_url)

    def _make_blog(self):
        form_data = {'title': 'one title', 'slug': 'one-title'}
        blog = Blog.objects.create(**form_data)
        blog.allowed_users.add(self.user)
        page_for_layouts = create_page(
            'master', 'page_template.html', language='en', published=True)
        blog_layout = Layout(**{
            'from_page': page_for_layouts,
            'content_object': blog,
            'layout_type': Blog.ALL
        })
        blog_layout.save()
        form_data.update({
            'allowed_users': [self.user.pk], 'layouts': [blog_layout.pk],
            'site': blog.site.pk})
        return blog, form_data

    def _make_entry(self, blog):
        return BlogEntryPage.objects.create(**{
            'title': 'first entry', 'blog': blog,
            'short_description': 'short_description'})

    def test_layouts_deletion(self):
        data = {'title': 'one title', 'slug': 'one-title'}
        blog = Blog.objects.create(**data)
        page_for_layouts = create_page(
            'master', 'page_template.html', language='en', published=True)

        slot_names = page_for_layouts.placeholders.values_list(
            'slot', flat=True)
        fixed_slots_len = len(get_fixed_section_slots(slot_names))
        # fixed placeholders are not used by layouts
        phds_count_for_layouts = (
            page_for_layouts.placeholders.count() -
            fixed_slots_len)

        for layout_type in Blog.LAYOUTS_CHOICES.keys():
            blog_layout = Layout(**{
                'from_page': page_for_layouts,
                'content_object': blog,
                'layout_type': layout_type
            })
            blog_layout.save()
            # generate layout placeholders
            url = reverse(
                'admin:cms_layouts_layout_change', args=(blog_layout.pk,))
            self.client.get(url)
            # add one plugin for a generated placeholder
            phd = blog_layout.hidden_placeholders[0]
            add_plugin(phd, 'TextPlugin', 'en', body=phd.slot)

        self.assertEquals(
            page_for_layouts.placeholders.model.objects.count(),
            phds_count_for_layouts * len(Blog.LAYOUTS_CHOICES) +
                page_for_layouts.placeholders.count())

        blog.delete()

        self.assertEquals(Layout.objects.count(), 0)
        self.assertEquals(
            page_for_layouts.placeholders.model.objects.count(),
            page_for_layouts.placeholders.count())

    def test_categories_deletion(self):
        blog, data = self._make_blog()
        form = forms.BlogForm(data=data, instance=blog)
        self.assertFalse(form.is_valid())
        categ = ['1one', '2two', '3three']
        data['categories'] = ', '.join(categ)
        form = forms.BlogForm(data=data, instance=blog)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEquals(blog.categories.count(), 3)
        self.assertItemsEqual(
            sorted(blog.categories.values_list('slug', flat=True)), categ)
        blog.categories.all()[0].delete()
        self.assertTrue(Blog.objects.filter(pk=blog.pk).exists())
        blog.delete()
        self.assertEquals(BlogCategory.objects.count(), 0)

    def test_dates_in_entries_slugs(self):
        blog, data = self._make_blog()
        entry = self._make_entry(blog=blog)
        entry_url = reverse(
            'cms_blogger.views.entry_or_bio_page', kwargs={
                'blog_slug': 'one-title',
                'slug': 'first-entry'})
        self.assertEquals(entry.get_absolute_url(), entry_url)
        blog.entries_slugs_with_date = True
        blog.save()
        entry_url = reverse('cms_blogger.views.entry_page', kwargs={
                'blog_slug': 'one-title',
                'year': entry.publication_date.year,
                'month': entry.publication_date.strftime('%m'),
                'day': entry.publication_date.strftime('%d'),
                'entry_slug': 'first-entry'})
        self.assertEquals(entry.get_absolute_url(), entry_url)

    def test_entries_deletion(self):
        blog, data = self._make_blog()
        data['categories'] = 'books'
        form = forms.BlogForm(data=data, instance=blog)
        form.is_valid()
        form.save()
        # when categ gets delete, entry remains
        entry = self._make_entry(blog=blog)
        entry.categories = blog.categories.all()
        categ_pk = blog.categories.all()[0].pk
        self.assertEquals(entry.categories.count(), 1)

        # change categ
        data['categories'] = 'other books'
        form = forms.BlogForm(data=data, instance=blog)
        form.is_valid()
        form.save()
        self.assertEquals(entry.categories.count(), 0)
        self.assertEquals(blog.categories.count(), 1)
        # first categ got deleted
        self.assertFalse(BlogCategory.objects.filter(pk=categ_pk).exists())
        self.assertTrue(
            BlogEntryPage.objects.filter(id=entry.id, blog=blog).exists())
        # blog should remain
        entry.delete()
        self.assertEquals(Blog.objects.count(), 1)
        # add another and delete the blog
        entry = self._make_entry(blog=blog)
        blog.delete()
        self.assertEquals(Blog.objects.count(), 0)
        self.assertEquals(BlogEntryPage.objects.count(), 0)

    def test_creation_workflow(self):
        add_url = reverse('admin:cms_blogger_blog_add')
        response = self.client.get(add_url)
        form = response.context_data['adminform'].form
        self.assertItemsEqual(sorted(form.fields.keys()), ['title', 'slug'])
        response = self.client.post(add_url, {
            'title': 'one title', 'slug': 'one-title'})
        self.assertEqual(response.status_code, 302)
        change_url = reverse('admin:cms_blogger_blog_change', args=(
            Blog.objects.all()[0].pk, ))
        response = self.client.get(change_url)
        form = response.context_data['adminform'].form
        change_fields = flatten_fieldsets(
            admin.BlogAdmin.change_form_fieldsets)
        readonly_fields = admin.BlogAdmin.readonly_in_change_form
        self.assertEquals(
            len(form.fields.keys()),
            len(change_fields) - len(readonly_fields))

    def tearDown(self):
        self.client.logout()


class TestChangeLists(TestCase):

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            'admin', 'admin@cms_blogger.com', 'secret')
        self.regular_user = User.objects.create_user(
            'regular', email='regular@cms_blogger.com', password='secret')
        self.regular_user.user_permissions = Permission.objects.all()
        self.regular_user.is_staff = True
        self.regular_user.save()
        # regular users will not see new sites blogs since the rule from
        #   cms_blogger.tests.utils.get_allowed_sites is applied
        self.new_site = Site.objects.create(
            name='new_site', domain='new_site.com')

    def test_site_session_changes_for_superuser(self):
        self.client.login(username='admin', password='secret')
        url = reverse('admin:cms_blogger_blog_changelist')
        response = self.client.get(url)
        self.assertCurrentSite(response, 1)
        response = self.client.get(url, {'site__exact': self.new_site.pk})
        self.assertCurrentSite(response, self.new_site.pk)
        self.client.logout()

    def test_site_session_changes_for_regular_user(self):
        self.client.login(username='regular', password='secret')
        url = reverse('admin:cms_blogger_blog_changelist')
        response = self.client.get(url)
        self.assertCurrentSite(response, 1)
        response = self.client.get(url, {'site__exact': 1})
        self.assertCurrentSite(response, 1)
        # even if the user requests a site that he has permissions on it
        #   should got to the default that he has access on
        response = self.client.get(url, {'site__exact': self.new_site.pk})
        self.assertCurrentSite(response, 1)
        self.client.logout()

    def assertCurrentSite(self, response, site):
        self.assertEquals(response.client.session['cms_admin_site'], site)
        self.assertEquals(response.context_data['cl'].current_site.pk, site)

    def _items(self, response):
        items = response.context_data['cl'].paginator
        return [el.pk for el in items.object_list]

    def test_blogs_displayed_by_site(self):
        self.client.login(username='admin', password='secret')
        url = reverse('admin:cms_blogger_blog_changelist')

        data = {'title': 'one title', 'slug': 'one-title'}
        b1 = Blog.objects.create(**data)

        response = self.client.get(url)
        self.assertItemsEqual(self._items(response), [b1.pk])
        # create a new one
        response = self.client.get(url, {'site__exact': self.new_site.pk})
        self.assertEquals(len(self._items(response)), 0)
        data.update({'site': self.new_site})
        b2 = Blog.objects.create(**data)
        # new site is still the current one
        response = self.client.get(url)
        self.assertItemsEqual(self._items(response), [b2.pk])

        response = self.client.get(url, {'site__exact': 1})
        self.assertItemsEqual(self._items(response), [b1.pk])

    def test_allowed_users_for_entries_list(self):
        data = {'title': 'one title', 'slug': 'one-title'}
        blog = Blog.objects.create(**data)
        entry = BlogEntryPage.objects.create(**{
            'title': 'first entry', 'blog': blog,
            'short_description': 'short_description'})

        url = reverse('admin:cms_blogger_blogentrypage_changelist')
        self.client.login(username='admin', password='secret')
        response = self.client.get(url)
        self.assertItemsEqual(self._items(response), [entry.pk])
        self.client.logout()

        self.client.login(username='regular', password='secret')
        response = self.client.get(url)
        self.assertEquals(len(self._items(response)), 0)
        blog.allowed_users.add(self.regular_user)
        response = self.client.get(url)
        self.assertItemsEqual(self._items(response), [entry.pk])
        self.client.logout()

    def test_allowed_users_for_entry_add_form(self):
        data = {'title': 'one title', 'slug': 'one-title'}
        blog = Blog.objects.create(**data)

        url = reverse('admin:cms_blogger_blogentrypage_add')
        self.client.login(username='admin', password='secret')
        response = self.client.get(url)
        qs = response.context_data['adminform'].form.fields['blog'].queryset
        self.assertEquals(len(qs), 1)
        self.client.logout()

        self.client.login(username='regular', password='secret')
        response = self.client.get(url)
        qs = response.context_data['adminform'].form.fields['blog'].queryset
        self.assertEquals(len(qs), 0)

        blog.allowed_users.add(self.regular_user)
        response = self.client.get(url)
        qs = response.context_data['adminform'].form.fields['blog'].queryset
        self.assertEquals(len(qs), 1)
        self.client.logout()


class TestBlogEntryModel(TestCase):

    def test_deletion(self):
        pass

    def test_next_prev_post(self):
        pass

    def test_draft(self):
        pass

    def test_publication_date_changes(self):
        pass

    def test_admin_publish_actions(self):
        pass

    def test_poster_image_deletion(self):
        pass


class TestNavigationMenu(TestCase):

    def test_blog_nodes_shown(self):
        pass


class TestAuthorModel(TestCase):

    def test_creation(self):
        pass

    def test_deletion(self):
        pass

    def test_form_initialization(self):
        pass


class TestBlogPageViews(TestCase):
    pass
