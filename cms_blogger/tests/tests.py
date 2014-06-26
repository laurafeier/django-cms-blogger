from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.sites.models import Site
from django.contrib.admin.util import flatten_fieldsets
from django.contrib.admin.sites import AdminSite
from django.core.urlresolvers import reverse
from django.template import Template
from django.utils import timezone
from django.test.client import RequestFactory
from dateutil import tz, parser

from cms_blogger.models import *
from cms_blogger import admin, forms
from cms.api import create_page, add_plugin
from cms.tests.menu import BaseMenuTest

from cms_blogger.admin import BlogEntryPageAdmin

from cms_layouts.models import Layout
from cms_layouts.layout_response import LayoutResponse
from cms_layouts.slot_finder import get_fixed_section_slots

import xml.etree.ElementTree
import urlparse
import urllib


class TestMoveAction(TestCase):
    def super_user(self):
        self.superuser = User.objects.create_superuser(
            'superuser', 'admin@cms_blogger.com', 'secret')
        self.superuser.is_active = True
        self.superuser.is_staff = True
        self.superuser.user_permissions = Permission.objects.all()
        self.superuser.save()
        self.client.login(username='superuser', password='secret')

    def regular_user(self):
        self.regularuser = User.objects.create_superuser(
            'regular', 'admin@cms_blogger.com', 'secret')
        self.regularuser.is_superuser = False
        self.regularuser.is_active = True
        self.regularuser.is_staff = True
        self.regularuser.user_permissions = Permission.objects.all()
        self.regularuser.save()
        self.client.login(username='regular', password='secret')

    def setUp(self):
        """
          B1   B2
        """
        self.blog1 = Blog.objects.create(**{
            'title': 'b1', 'slug': 'b1'})
        self.blog2 = Blog.objects.create(**{
            'title': 'b2', 'slug': 'b2'})
        self.CAT1_NAME = "cat1"

    def assert_one_category(self, blog):
        self.assertEquals(
            1,
            blog.categories.count(),
            "Blog %s should have only one category")

    def assert_entry_tied_to_blog(self, e1, blog):
        self.assertEqual(
            e1.blog.id,
            blog.id,
            'entry should be linked to new blog')

    def assert_entry_has_category(self, entry, category_name):
        try:
            entry.categories.get(name=category_name)
        except:
            self.fail("Entry %s should have category %s" % (
                entry.title,
                category_name))

    def assert_blog_has_category(self, blog, category_name):
        try:
            blog.categories.get(name=category_name)
        except:
            self.fail("Blog %s should have category %s" % (
                blog.title,
                category_name))

    def assert_blog_has_no_category(self, blog):
        self.assertEquals(
            False,
            blog.categories.exists(),
            "Blog %s should have no categories" % (
                blog.title))

    def move_entries(self, destination_blog, entries, mirror_categories=True):
        data = {
            'apply': 'Move',
            'entries': [x.id for x in entries],
            'destination_blog': destination_blog.id}
        if mirror_categories:
            data.update({'mirror_categories': 'on'})

        url = '%s?%s' % (
            reverse('admin:cms_blogger-move-entries'),
            urllib.urlencode({x.id: "" for x in entries}))
        return self.client.post(url, data, follow=True)

    def create_category(self, blog, category_name=None):
        category_name = category_name or self.CAT1_NAME
        return BlogCategory.objects.create(
            name=category_name,
            blog=blog)

    def create_entry(self, blog, title='e1', save=True):
        entry = BlogEntryPage.objects.create(
            title=title,
            blog=blog,
            short_description=title)
        if save:
            entry.save()
        return entry

    def test_simple_move_draft(self):
        """
          B1  B2   >   B1  B2
         /         >      /
        E1         >     E1
        """
        self.super_user()
        self.e1 = self.create_entry(self.blog1, save=False)
        self.move_entries(self.blog2, [self.e1])

        e1 = BlogEntryPage.objects.get(id=self.e1.id)
        blog2 = Blog.objects.get(id=self.blog2.id)

        self.assert_entry_tied_to_blog(e1, blog2)

    def test_simple_move(self):
        """
          B1  B2   >   B1  B2
         /         >      /
        E1         >     E1
        """
        self.super_user()
        self.e1 = self.create_entry(self.blog1)
        self.move_entries(self.blog2, [self.e1])

        e1 = BlogEntryPage.objects.get(id=self.e1.id)
        blog2 = Blog.objects.get(id=self.blog2.id)

        self.assert_entry_tied_to_blog(e1, blog2)

    def test_move_blogentry_mirror_category(self):
        """
        mirror category
          B1      B2   >   B1    B2
         /  \          >        /  \
        E1 = C1        >       E1 = C1
        """
        self.super_user()
        self.e1 = self.create_entry(self.blog1)
        self.cat1 = self.create_category(blog=self.blog1)
        self.e1.categories.add(self.cat1)
        self.move_entries(self.blog2, [self.e1, ])

        e1 = BlogEntryPage.objects.get(id=self.e1.id)
        blog1 = Blog.objects.get(id=self.blog1.id)
        blog2 = Blog.objects.get(id=self.blog2.id)

        self.assert_entry_tied_to_blog(e1, blog2)
        self.assert_blog_has_no_category(blog1)
        self.assert_blog_has_category(blog2, self.CAT1_NAME)

    def test_move_blogentry_no_mirror_category(self):
        """
        no category mirroring
          B1      B2   >   B1    B2
         /  \          >        /
        E1 = C1        >       E1
        """
        self.super_user()
        self.e1 = self.create_entry(self.blog1)
        self.cat1 = self.create_category(self.blog1)

        self.e1.categories.add(self.cat1)
        self.move_entries(self.blog2, [self.e1, ], mirror_categories=False)

        e1 = BlogEntryPage.objects.get(id=self.e1.id)
        blog1 = Blog.objects.get(id=self.blog1.id)
        blog2 = Blog.objects.get(id=self.blog2.id)

        self.assert_entry_tied_to_blog(e1, blog2)
        self.assert_blog_has_no_category(blog2)
        self.assert_blog_has_no_category(blog1)

    def test_move_blogentry_no_mirror_already_existing_category(self):
        """
        no category mirroring
          B1      B2      >   B1    B2
         /  \       \     >        /  \
        E1 = C1      C1   >       E1 = C1
        """

        self.super_user()
        self.e1 = self.create_entry(self.blog1)

        self.b1cat1 = self.create_category(self.blog1)
        self.b1cat2 = self.create_category(self.blog2)
        self.e1.categories.add(self.b1cat1)

        self.move_entries(self.blog2, [self.e1, ], mirror_categories=False)

        e1 = BlogEntryPage.objects.get(id=self.e1.id)
        blog1 = Blog.objects.get(id=self.blog1.id)
        blog2 = Blog.objects.get(id=self.blog2.id)

        self.assert_entry_tied_to_blog(e1, blog2)
        self.assert_entry_has_category(e1, self.CAT1_NAME)
        self.assert_blog_has_category(blog2, self.CAT1_NAME)
        self.assert_blog_has_no_category(blog1)

    def test_move_blogentry_w_mirror_and_already_existing_category(self):
        """
        mirror category
          B1      B2      >   B1    B2
         /  \       \     >        /  \
        E1 = C1      C1   >       E1 = C1
        """
        self.super_user()
        self.e1 = self.create_entry(self.blog1)

        self.b1cat1 = self.create_category(self.blog1)
        self.b1cat2 = self.create_category(self.blog2)
        self.e1.categories.add(self.b1cat1)

        self.move_entries(self.blog2, [self.e1, ])

        e1 = BlogEntryPage.objects.get(id=self.e1.id)
        blog1 = Blog.objects.get(id=self.blog1.id)
        blog2 = Blog.objects.get(id=self.blog2.id)

        self.assert_entry_tied_to_blog(e1, blog2)
        self.assert_entry_has_category(e1, self.CAT1_NAME)
        self.assert_blog_has_category(blog2, self.CAT1_NAME)
        self.assert_one_category(blog2)
        self.assert_blog_has_no_category(blog1)

    def test_entry_slug_collision1(self):
        """
        entries with same title
              B1           B2        >    B1       B2......
             /  \         /  \       >            / /      \
        E1(e1) = C1  E2(e1) = C1     >    E1(e1-1),E2(e1) = C1
        """

        self.super_user()
        self.e1 = self.create_entry(self.blog1)
        self.e2 = self.create_entry(self.blog2)
        self.e1.save()
        self.e2.save()

        self.cat1 = self.create_category(self.blog1)
        self.e1.categories.add(self.cat1)

        self.cat2 = self.create_category(self.blog2)
        self.e2.categories.add(self.cat2)

        self.e1.save()
        self.e2.save()

        self.move_entries(self.blog2, [self.e1, ])

        e1 = BlogEntryPage.objects.get(id=self.e1.id)
        e2 = BlogEntryPage.objects.get(id=self.e2.id)
        blog1 = Blog.objects.get(id=self.blog1.id)
        blog2 = Blog.objects.get(id=self.blog2.id)

        self.assert_entry_tied_to_blog(e1, blog2)
        self.assert_entry_tied_to_blog(e2, blog2)
        self.assert_entry_has_category(e1, self.CAT1_NAME)
        self.assert_entry_has_category(e2, self.CAT1_NAME)
        self.assertNotEqual(
            e1.slug,
            e2.slug,
            "Entries should have different slugs "
            "since they are in the same blog")
        self.assert_one_category(blog2)
        self.assert_blog_has_category(blog2, self.CAT1_NAME)
        self.assert_blog_has_no_category(blog1)

    def test_entry_slug_collision2(self):
        """
        entries with same title
              B1           B2    B3  >  B1 B2      B3........
             /  \         /  \       >            / /        \
        E1(e1) = C1  E2(e1) = C1     >      E1(e1),E2(e1-1) = C1
        """

        self.super_user()
        self.e1 = self.create_entry(self.blog1)
        self.blog3 = Blog.objects.create(**{
            'title': 'b3', 'slug': 'b3'})

        self.e2 = self.create_entry(self.blog2)

        self.cat1 = self.create_category(self.blog1)
        self.e1.categories.add(self.cat1)

        self.cat2 = self.create_category(self.blog2)
        self.e2.categories.add(self.cat2)

        self.e1.save()
        self.e2.save()

        self.move_entries(self.blog3, [self.e1, self.e2])

        e1 = BlogEntryPage.objects.get(id=self.e1.id)
        e2 = BlogEntryPage.objects.get(id=self.e2.id)
        blog1 = Blog.objects.get(id=self.blog1.id)
        blog2 = Blog.objects.get(id=self.blog2.id)
        blog3 = Blog.objects.get(id=self.blog3.id)

        self.assert_entry_tied_to_blog(e1, blog3)
        self.assert_entry_tied_to_blog(e2, blog3)
        self.assert_entry_has_category(e1, self.CAT1_NAME)
        self.assert_entry_has_category(e2, self.CAT1_NAME)
        self.assertNotEqual(
            e1.slug,
            e2.slug,
            "Entries should have different slugs "
            "since they are in the same blog")
        self.assert_one_category(blog3)
        self.assert_blog_has_category(blog3, self.CAT1_NAME)
        self.assert_blog_has_no_category(blog1)
        self.assert_blog_has_no_category(blog2)

    def test_move_to_same(self):
        """
          B1       >      B1
         /  \      >     /  \
        E1 = C1    >    E1 = C1
        """
        self.super_user()
        self.e1 = self.create_entry(self.blog1)
        self.cat1 = self.create_category(self.blog1)
        self.e1.categories.add(self.cat1)

        response = self.move_entries(self.blog1, [self.e1, ])

        messages = [m.message for m in response.context['messages']]

        self.assertTrue(messages)
        self.assertIn("already present", messages[0])

    def test_attempt_move_to_same_blog(self):
        """
        move both to B2
              B1        B2   >
             /         /     >  warn user he's attempting to move
        E1(e1)    E2(e1)     >  an entry to the same blog
        """
        self.super_user()
        self.e1 = self.create_entry(self.blog1)
        self.e2 = self.create_entry(self.blog2)

        response = self.move_entries(self.blog2, [self.e1, self.e2])
        messages = [m.message for m in response.context['messages']]
        e1 = BlogEntryPage.objects.get(id=self.e1.id)
        blog1 = Blog.objects.get(id=self.blog1.id)

        self.assertTrue(messages)
        self.assertIn("Entry e1 was already present in blog b2", messages[0])

        #test it didn't move
        self.assert_entry_tied_to_blog(e1, blog1)

    def test_move_nothing(self):
        self.super_user()
        response = self.move_entries(self.blog2, [])
        messages = [m.message for m in response.context['messages']]
        self.assertTrue(messages)
        self.assertIn("There are no entries selected.", messages[0])

    def test_attempt_move_by_sneaky_regularuser(self):
        self.regular_user()
        response = self.move_entries(self.blog2, [])
        messages = [m.message for m in response.context['messages']]
        self.assertTrue(messages)
        self.assertIn(
            "Only superusers are allowed to move blog entries",
            messages[0])

    def test_move_action_exists_in_dropdown(self):
        self.super_user()
        response = self.move_entries(self.blog2, [])
        request = RequestFactory().get('/admin/cms_blogger/blogentrypage/')
        request.user = self.superuser

        admin = BlogEntryPageAdmin(BlogEntryPage, AdminSite())
        actions = admin.get_actions(request)
        self.assertIn("move_entries", actions.keys())

    def test_move_action_does_not_exist_in_dropdown(self):
        self.regular_user()
        response = self.move_entries(self.blog2, [])
        request = RequestFactory().get('/admin/cms_blogger/blogentrypage/')
        request.user = self.regularuser

        admin = BlogEntryPageAdmin(BlogEntryPage, AdminSite())
        actions = admin.get_actions(request)
        self.assertNotIn("move_entries", actions.keys())


class TestBlogModel(TestCase):

    def setUp(self):
        superuser = User.objects.create_superuser(
            'admin', 'admin@cms_blogger.com', 'secret')
        self.client.login(username='admin', password='secret')
        self.user = superuser

    def test_urls(self):
        self._make_blog()
        blog = Blog.objects.all().get()
        resp_code = lambda x: self.client.get(x).status_code
        self.assertEquals(resp_code('/aa_blogs/'), 404)
        # proxied sites need to have a rewrite rule similar to:
        # ^/(<proxy-prefix>/blogs(|/.*))$ proxy:http://<site-hostname>/blogs$2
        self.assertEquals(resp_code('/proxied/blogs/'), 404)
        self.assertEquals(resp_code('/i/am/proxied/too/blogs/'), 404)
        self.assertEquals(resp_code('/blogs/'), 200)
        self.assertEquals(resp_code('/blogs/one-title/'), 200)
        self.assertEquals(resp_code('/blogs/one-title/none/'), 404)
        self.assertEquals(resp_code('/blogs/one-title/category/music/'), 404)
        categ = BlogCategory.objects.create(blog=blog, name='music')
        self.assertEquals(resp_code('/blogs/one-title/category/music/'), 200)
        self.assertEquals(resp_code('/blogs/one-title/first-entry/'), 404)
        entry = self._make_entry(blog)
        self.assertEquals(resp_code('/blogs/one-title/first-entry/'), 404)
        self.assertEquals(resp_code('/blogs/one-title/first-entry/?preview'), 200)
        entry.is_published = True
        entry.save()
        self.assertEquals(resp_code('/blogs/one-title/first-entry/'), 200)

    def test_creation(self):
        # only title and slug are required fields
        # at least one page is required
        create_page('master', 'page_template.html',
                    language='en', published=True)
        data = {'title': 'one title', 'slug': 'one-title'}
        add_url = reverse('admin:cms_blogger_blog_add')
        self.client.post(add_url, data)
        # blog site should be prepopulated with the current site
        blog = Blog.objects.all().get()
        self.assertEquals(blog.site.pk, 1)
        # current user should be added
        self.assertEquals(blog.allowed_users.all().get().pk, self.user.pk)
        landing_url = reverse('cms_blogger.views.landing_page', kwargs={
            'blog_slug': 'one-title'})
        self.assertEquals(blog.get_absolute_url(), landing_url)
        self.assertEquals(self.client.get(landing_url).status_code, 200)

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
        entry_url = reverse(
            'cms_blogger.views.entry_page', kwargs={
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
        create_page('master', 'page_template.html',
                    language='en', published=True)
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

    def test_user_sees_only_accessible_entries(self):
        self.client.login(username='regular', password='secret')
        self.blog1 = Blog.objects.create(**{
            'title': 'b1', 'slug': 'b1'})
        self.blog1.allowed_users.add(self.regular_user)

        self.blog2 = Blog.objects.create(**{
            'title': 'b2', 'slug': 'b2'})

        self.entry1 = BlogEntryPage.objects.create(
            title="e1", blog=self.blog1, short_description="e1")
        self.entry2 = BlogEntryPage.objects.create(
            title="e2", blog=self.blog2, short_description="e2")

        url = reverse('admin:cms_blogger_blogentrypage_changelist')
        response = self.client.get(url)
        self.assertItemsEqual(self._items(response), [self.entry1.pk])

        url2 = '%s?%s' % (
            reverse('admin:cms_blogger_blogentrypage_changelist'),
            urllib.urlencode({"q": "e"}))
        response = self.client.get(url)
        self.assertItemsEqual(self._items(response), [self.entry1.pk])
        self.client.logout()


class TestBlogEntryModel(TestCase):

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            'admin', 'admin@cms_blogger.com', 'secret')
        self.client.login(username='admin', password='secret')
        self.blog = Blog.objects.create(**{
            'title': 'one title', 'slug': 'one-title'})

    def tearDown(self):
        self.client.logout()

    def test_content_deletion(self):
        entry = BlogEntryPage.objects.create(**{
            'title': 'first entry', 'blog': self.blog,
            'short_description': 'desc'})
        entry.content_body = 'custom text'
        entry.save()
        Placeholder = entry.content.__class__
        CMSPlugin = entry.content.cmsplugin_set.model
        self.assertEquals(Placeholder.objects.count(), 1)
        self.assertEquals(CMSPlugin.objects.count(), 1)
        self.assertEquals(entry.get_content_plugin().body, 'custom text')

        blog_id = self.blog.pk
        entry.delete()
        self.assertEquals(Placeholder.objects.count(), 0)
        self.assertEquals(CMSPlugin.objects.count(), 0)
        self.assertTrue(Blog.objects.filter(pk=self.blog.pk).exists())

    def test_next_prev_post_even(self):
        for i in range(4):
            BlogEntryPage.objects.create(**{
                'title': '%s' % i, 'blog': self.blog,
                'short_description': 'desc', 'is_published': True})
        BlogEntryPage.objects.update(publication_date=timezone.now())
        entries = {e.title: e for e in BlogEntryPage.objects.all()}

        self.assertEquals(entries["0"].previous_post(), None)
        self.assertEquals(entries["0"].next_post().pk, entries["1"].pk)
        self.assertEquals(entries["1"].previous_post().pk, entries["0"].pk)
        self.assertEquals(entries["1"].next_post().pk, entries["2"].pk)
        self.assertEquals(entries["2"].previous_post().pk, entries["1"].pk)
        self.assertEquals(entries["2"].next_post().pk, entries["3"].pk)
        self.assertEquals(entries["3"].previous_post().pk, entries["2"].pk)
        self.assertEquals(entries["3"].next_post(), None)

    def test_next_prev_post_odd(self):
        for i in range(5):
            BlogEntryPage.objects.create(**{
                'title': '%s' % i, 'blog': self.blog,
                'short_description': 'desc', 'is_published': True})
        BlogEntryPage.objects.update(publication_date=timezone.now())
        entries = {e.title: e for e in BlogEntryPage.objects.all()}

        self.assertEquals(entries["0"].previous_post(), None)
        self.assertEquals(entries["0"].next_post().pk, entries["1"].pk)
        self.assertEquals(entries["1"].previous_post().pk, entries["0"].pk)
        self.assertEquals(entries["1"].next_post().pk, entries["2"].pk)
        self.assertEquals(entries["2"].previous_post().pk, entries["1"].pk)
        self.assertEquals(entries["2"].next_post().pk, entries["3"].pk)
        self.assertEquals(entries["3"].previous_post().pk, entries["2"].pk)
        self.assertEquals(entries["3"].next_post().pk, entries["4"].pk)
        self.assertEquals(entries["4"].previous_post().pk, entries["3"].pk)
        self.assertEquals(entries["4"].next_post(), None)

    def test_draft(self):
        draft_entry = BlogEntryPage.objects.create(blog=self.blog)
        self.assertTrue(draft_entry.is_draft)
        url = reverse('admin:cms_blogger_blogentrypage_change',
                      args=(draft_entry.pk, ))
        response = self.client.get(url)
        data = response.context_data['adminform'].form.initial
        data['title'] = '@@#@$$##%&&**(*(*^&(^&<>?<~~~!)'
        response = self.client.post(url, data)
        self.assertTrue(len(response.context_data['errors']) >= 1)
        data['title'] = 'Sample title'
        data['short_description'] = 'short_description'
        response = self.client.post(url, data)
        self.assertEquals(response.status_code, 302)
        self.assertFalse(BlogEntryPage.objects.get(id=draft_entry.id).is_draft)

    def test_publication_date_changes(self):
        entry = BlogEntryPage.objects.create(**{
            'title': 'entry', 'blog': self.blog,
            'short_description': 'desc'})
        self.assertEquals(entry.slug, 'entry')
        self.assertFalse(entry.is_draft)
        default_pub_date = entry.publication_date

        url = reverse('admin:cms_blogger_blogentrypage_change',
                      args=(entry.pk, ))
        response = self.client.get(url)

        data = response.context_data['adminform'].form.initial
        data['_pub_pressed'] = True
        response = self.client.post(url, data)
        # should reset
        entry = BlogEntryPage.objects.get(id=entry.id)
        self.assertNotEquals(default_pub_date, entry.publication_date)
        self.assertTrue(entry.is_published)
        # unpublish
        response = self.client.post(url, data)
        entry = BlogEntryPage.objects.get(id=entry.id)
        self.assertFalse(entry.is_published)
        # publish with start date
        data['start_publication'] = '05/06/2014 11:51 AM'
        data['_start_publication_tzoffset'] = '+03:00'
        response = self.client.post(url, data)
        entry = BlogEntryPage.objects.get(id=entry.id)
        start_date_str = ' '.join([data['start_publication'],
                                   data['_start_publication_tzoffset']])
        start_date = parser.parse(start_date_str).astimezone(tz.tzutc())
        self.assertEquals(start_date, entry.publication_date)
        self.assertTrue(entry.is_published)

    def test_admin_publish_actions(self):
        for i in range(4):
            BlogEntryPage.objects.create(**{
                'title': 'entry', 'blog': self.blog,
                'short_description': 'desc'})
        self.assertEquals(len(self.blog.get_entries()), 0)
        entries_ids = BlogEntryPage.objects.values_list('id', flat=True)
        url = reverse('admin:cms_blogger_blogentrypage_changelist')
        response = self.client.post(url, {
            '_selected_action': entries_ids,
            'action': 'make_published',
            'post': 'yes', })
        self.assertEquals(self.blog.get_entries().count(), len(entries_ids))

        response = self.client.post(url, {
            '_selected_action': entries_ids,
            'action': 'make_unpublished',
            'post': 'yes', })
        self.assertEquals(self.blog.get_entries().count(), 0)

    def test_poster_image_deletion(self):
        pass

    def test_title_rendering(self):
        page_for_layouts = create_page(
            'master', 'page_template.html', language='en', published=True)
        Layout.objects.create(**{
            'from_page': page_for_layouts,
            'content_object': self.blog,
            'layout_type': Blog.ALL})
        entry = BlogEntryPage.objects.create(**{
            'title': 'Hello', 'blog': self.blog, 'is_published': True,
            'short_description': 'I am a blog entry',
            'meta_keywords': "article,blog,keyword", })
        # make request to get all the cms midlleware data
        resp = self.client.get(page_for_layouts.get_absolute_url())
        # request with all middleware data
        request = resp.context['request']
        # build a layout response to use its context for another template
        resp = LayoutResponse(entry, entry.get_layout(), request)
        # we dont need the http response but we need the context that holds
        # the title
        resp.make_response()
        self.assertEquals(Template(
            "{% load cms_tags %}"
            "{% page_attribute title %} "
            "{% page_attribute meta_description %} "
            "{% page_attribute meta_keywords %}").render(resp.context),
            "Hello I am a blog entry article,blog,keyword")


class TestNavigationMenu(BaseMenuTest):

    def setUp(self):
        super(TestNavigationMenu, self).setUp()
        self.blog1 = Blog.objects.create(**{
            'in_navigation': True, 'title': '1', 'slug': '1'})
        self.blog2 = Blog.objects.create(**{
            'in_navigation': True, 'title': '2', 'slug': '2'})

    def _menu_nodes(self):
        context = self.get_context()
        tpl = Template(
            "{% load menu_tags %}"
            "{% show_menu 0 1 1 100 'admin/cms_blogger/blog/menu_nodes.html' %}")
        tpl.render(context)
        return context['children']

    def test_blog_not_in_navigation(self):
        self.assertEquals(len(self._menu_nodes()), 0)
        node1 = BlogNavigationNode.objects.create(position=0, text='1')
        self.blog1.navigation_node = node1
        self.blog1.in_navigation = False
        self.blog1.save()
        self.assertEquals(len(self._menu_nodes()), 0)

    def test_blog_root_nodes_in_nav(self):
        self.assertEquals(len(self._menu_nodes()), 0)
        node1 = BlogNavigationNode.objects.create(position=0, text='1')
        self.blog1.navigation_node = node1
        self.blog1.save()
        self.assertEquals(len(self._menu_nodes()), 1)
        # add another before the first one
        node2 = BlogNavigationNode.objects.create(position=0, text='2')
        self.blog2.navigation_node = node2
        self.blog2.save()
        nodes_texts = [n.title for n in self._menu_nodes()]
        self.assertEquals(len(nodes_texts), 2)
        self.assertEquals(nodes_texts[0], '2')
        self.assertEquals(nodes_texts[1], '1')
        # move node2 after node1
        node2.position = 1
        node2.save()
        nodes_texts = [n.title for n in self._menu_nodes()]
        self.assertEquals(len(nodes_texts), 2)
        self.assertEquals(nodes_texts[0], '1')
        self.assertEquals(nodes_texts[1], '2')
        # empty menu
        self.blog1.delete()
        self.blog2.delete()
        self.assertEquals(len(self._menu_nodes()), 0)

    def test_blog_child_nodes_in_nav(self):
        self.assertEquals(len(self._menu_nodes()), 0)
        # parent_node_id
        node = BlogNavigationNode.objects.create(position=0, text='1')
        self.blog1.navigation_node = node
        self.blog1.save()
        self.assertEquals(len(self._menu_nodes()), 1)
        # add child
        # blog parent nav node ids have negative numbers in order to
        #   distinguish them from the page ids
        child = BlogNavigationNode.objects.create(
            position=0, text='2', parent_node_id=node.id * -1)
        self.blog2.navigation_node = child
        self.blog2.save()
        nodes_texts = [n.title for n in self._menu_nodes()]
        self.assertItemsEqual(nodes_texts, ['1'])
        children = self._menu_nodes()[0].children
        child_node = children[0]
        self.assertEquals(child_node.title, '2')
        self.assertEquals(len(children), 1)
        # change parent_id to a positive number => no nav node children since
        #       there are no pages with that id
        child.parent_node_id = 1
        child.save()
        nodes_texts = [n.title for n in self._menu_nodes()]
        self.assertEquals(len(nodes_texts), 1)
        self.assertEquals(len(self._menu_nodes()[0].children), 0)


class TestAuthorModel(TestCase):

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            'admin', 'admin@cms_blogger.com', 'secret')
        self.client.login(username='admin', password='secret')
        self.blog = Blog.objects.create(**{
            'title': 'one title', 'slug': 'one-title'})
        self.entry = BlogEntryPage.objects.create(**{
            'title': 'first entry', 'blog': self.blog,
            'short_description': 'short_description'})
        self.entry_url = reverse(
            'admin:cms_blogger_blogentrypage_change', args=(self.entry.pk, ))

    def tearDown(self):
        self.client.logout()

    def test_creation(self):
        response = self.client.get(self.entry_url)
        self.assertEquals(self.entry.authors.count(), 0)
        superuser_author = Author.objects.all()[0]
        initial = response.context_data['adminform'].form.initial
        initial['authors'] = [superuser_author.pk]
        self.client.post(self.entry_url, initial)
        self.assertEquals(self.entry.authors.count(), 1)
        initial['authors'] = [superuser_author.pk, 'new_author']
        self.client.post(self.entry_url, initial)
        self.assertEquals(Author.objects.count(), 2)
        self.assertEquals(self.entry.authors.count(), 2)

    def test_user_deletion(self):
        new_user = User.objects.create_superuser(
            'new_user', 'admin2@cms_blogger.com', 'secret')
        response = self.client.get(self.entry_url)
        self.assertEquals(Author.objects.count(), 2)
        new_user.delete()
        self.assertEquals(Author.objects.count(), 2)
        Author.objects.get(name='admin2@cms_blogger.com')

    def test_form_initialization(self):
        self.assertEquals(Author.objects.count(), 0)
        self.client.get(self.entry_url)
        self.assertEquals(Author.objects.count(), 1)

    def test_unused_authors_removal(self):
        User.objects.create_superuser(
            'new_user', 'admin2@cms_blogger.com', 'secret')
        Author.objects.create(name='custom author')
        # generate authors
        response = self.client.get(self.entry_url)
        self.assertEquals(Author.objects.count(), 3)
        superuser_author = Author.objects.get(user=self.superuser.id)

        new_entry = BlogEntryPage.objects.create(**{
            'title': 'new entry', 'blog': self.blog,
            'short_description': 'short_description'})
        # add authors
        new_entry.authors.add(*Author.objects.all())
        self.entry.authors.add(*Author.objects.all())

        # set only a default author so that requred validation error
        #   is not raised
        response = self.client.get(self.entry_url)
        initial = response.context_data['adminform'].form.initial
        initial['authors'] = [superuser_author.pk]
        self.assertEquals(self.entry.authors.count(), 3)
        self.client.post(self.entry_url, initial)
        self.assertEquals(self.entry.authors.count(), 1)

        # no authors should get deleted since all are in use by the other entry
        self.assertEquals(Author.objects.count(), 3)

        # set the default author for the other entry
        new_entry_url = reverse(
            'admin:cms_blogger_blogentrypage_change', args=(new_entry.pk, ))
        response = self.client.get(new_entry_url)
        self.assertEquals(new_entry.authors.count(), 3)
        initial = response.context_data['adminform'].form.initial
        initial['authors'] = [superuser_author.pk]
        self.client.post(new_entry_url, initial)
        self.assertEquals(new_entry.authors.count(), 1)

        # only custom author should get deleted since it's not in use and the
        #   authors generated from users should never get deleted
        self.assertEquals(Author.objects.count(), 2)


class TestBlogPageViews(TestCase):
    pass


class TestSitemap(TestCase):

    def setUp(self):
        self.url = reverse('blogger-sitemap')
        self.location_tag = '{http://www.sitemaps.org/schemas/sitemap/0.9}loc'
        self.lastmod_tag = '{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod'

    def assert_status_ok(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def assert_is_empty(self, obj):
        self.assertEqual(0, len(obj))

    def assert_is_not_empty(self, obj):
        self.assertNotEqual(0, len(obj))

    def assert_blog_landingpage(self, blog, location):
        site = Site.objects.get_current()
        url_parts = urlparse.urlparse(location)
        blog_path = blog.get_absolute_url()
        self.assertEqual(blog_path, url_parts.path)
        self.assertEqual(site.domain, url_parts.netloc)

    def assert_blogentry_location(self, blogentry, location):
        site = Site.objects.get_current()
        url_parts = urlparse.urlparse(location)
        entry_path = blogentry.get_absolute_url()
        self.assertEqual(entry_path, url_parts.path)
        self.assertEqual(site.domain, url_parts.netloc)

    def assert_blogcategory_location(self, blogcategory, location):
        site = Site.objects.get_current()
        url_parts = urlparse.urlparse(location)
        category_path = blogcategory.get_absolute_url()
        self.assertEqual(category_path, url_parts.path)
        self.assertEqual(site.domain, url_parts.netloc)

    def sitemap_locations(self, xml_string):
        xml_tree = xml.etree.ElementTree.fromstring(xml_string)
        location_iterator = xml_tree.iter(self.location_tag)
        locations = map(lambda node: node.text, location_iterator)
        return locations

    def sitemap_lastmods(self, xml_string):
        xml_tree = xml.etree.ElementTree.fromstring(xml_string)
        lastmod_iterator = xml_tree.iter(self.lastmod_tag)
        lastmods = map(lambda node: node.text, lastmod_iterator)
        return lastmods

    def url_path(self, url):
        url_parts = urlparse.urlparse(url)
        path = url_parts.path
        return path

    def make_entry(self, blog, suffix, is_published=True):
        params = {
            'title': 'title_{suffix}'.format(suffix=suffix),
            'slug': 'slug_{suffix}'.format(suffix=suffix),
            'short_description': 'description_{suffix}'.format(suffix=suffix),
            'is_published': is_published,
            'blog': blog,
        }
        entry = BlogEntryPage.objects.create(**params)
        return entry

    def make_category(self, blog, suffix, *entries):
        params = {
            'name': 'category_{suffix}'.format(suffix=suffix),
            'slug': 'slug_{suffix}'.format(suffix=suffix),
            'blog': blog,
        }
        category = BlogCategory.objects.create(**params)
        for entry in entries:
            category.entries.add(entry)
        category.save()
        return category

    def test_baseview(self):
        self.assert_status_ok(self.url)

    def test_empty(self):
        response = self.client.get(self.url)
        locations = self.sitemap_locations(response.content)
        self.assert_is_empty(locations)

    def test_one_blog(self):
        blog = Blog.objects.create(title='test_blog', slug='test_blog')
        response = self.client.get(self.url)
        locations = self.sitemap_locations(response.content)
        self.assert_is_not_empty(locations)
        self.assertEqual(len(locations), 1)
        self.assert_blog_landingpage(blog, locations[0])

    def test_many_blogs(self):
        blog_one = Blog.objects.create(title='blog_one', slug='blog_one')
        blog_two = Blog.objects.create(title='blog_two', slug='blog_two')
        response = self.client.get(self.url)
        locations = self.sitemap_locations(response.content)
        self.assert_is_not_empty(locations)
        self.assertEqual(len(locations), 2)
        self.assert_blog_landingpage(blog_one, locations[0])
        self.assert_blog_landingpage(blog_two, locations[1])

    def test_one_blog_one_entry(self):
        blog = Blog.objects.create(title='test_blog', slug='test_blog')
        entry = self.make_entry(blog, suffix='single')
        response = self.client.get(self.url)
        locations = self.sitemap_locations(response.content)
        self.assert_is_not_empty(locations)
        self.assertEqual(len(locations), 2)
        self.assert_blog_landingpage(blog, locations[0])
        self.assert_blogentry_location(entry, locations[1])

    def test_one_blog_many_entries(self):
        blog = Blog.objects.create(title='test_blog', slug='test_blog')
        one = self.make_entry(blog, suffix='one')
        two = self.make_entry(blog, suffix='two')
        response = self.client.get(self.url)
        locations = self.sitemap_locations(response.content)
        self.assert_is_not_empty(locations)
        self.assertEqual(len(locations), 3)
        self.assert_blog_landingpage(blog, locations[0])
        self.assert_blogentry_location(one, locations[1])
        self.assert_blogentry_location(two, locations[2])

    def test_one_category(self):
        blog = Blog.objects.create(title='test_blog', slug='test_blog')
        entry = self.make_entry(blog, suffix='single')
        category = self.make_category(blog, 'category', entry)
        response = self.client.get(self.url)
        locations = self.sitemap_locations(response.content)
        self.assert_is_not_empty(locations)
        self.assertEqual(len(locations), 3)
        self.assert_blog_landingpage(blog, locations[0])
        self.assert_blogentry_location(entry, locations[1])
        self.assert_blogcategory_location(category, locations[2])

    def test_entries_same_categories(self):
        blog = Blog.objects.create(title='test_blog', slug='test_blog')
        entry_one = self.make_entry(blog=blog, suffix='one')
        entry_two = self.make_entry(blog=blog, suffix='two')
        category = self.make_category(blog, 'category', entry_one, entry_two)
        response = self.client.get(self.url)
        locations = self.sitemap_locations(response.content)
        self.assert_is_not_empty(locations)
        self.assertEqual(len(locations), 4)
        self.assert_blog_landingpage(blog, locations[0])
        self.assert_blogentry_location(entry_one, locations[1])
        self.assert_blogentry_location(entry_two, locations[2])
        self.assert_blogcategory_location(category, locations[3])

    def test_entries_different_categories(self):
        blog = Blog.objects.create(title='test_blog', slug='test_blog')
        entry_one = self.make_entry(blog=blog, suffix='one')
        entry_two = self.make_entry(blog=blog, suffix='two')
        category_one = self.make_category(blog, 'category_one', entry_two)
        category_two = self.make_category(blog, 'category_two', entry_two)
        response = self.client.get(self.url)
        locations = self.sitemap_locations(response.content)
        self.assert_is_not_empty(locations)
        self.assertEqual(len(locations), 5)
        self.assert_blog_landingpage(blog, locations[0])
        self.assert_blogentry_location(entry_one, locations[1])
        self.assert_blogentry_location(entry_two, locations[2])
        self.assert_blogcategory_location(category_one, locations[3])
        self.assert_blogcategory_location(category_two, locations[4])

    def test_lastmod(self):
        blog = Blog.objects.create(title='test_blog', slug='test_blog')
        entry = self.make_entry(blog, suffix='single')
        category = self.make_category(blog, 'category', entry)
        response = self.client.get(self.url)
        locations = self.sitemap_locations(response.content)
        lastmods = self.sitemap_lastmods(response.content)
        self.assertEqual(len(locations), len(lastmods))
        for lastmod in lastmods:
            self.assertIsNot(lastmod, None)
