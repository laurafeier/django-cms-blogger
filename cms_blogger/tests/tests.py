from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.sites.models import Site
from django.contrib.admin.util import flatten_fieldsets
from django.core.urlresolvers import reverse
from django.template import Template
from dateutil import tz, parser

from cms_blogger.models import *
from cms_blogger import admin, forms
from cms.api import create_page, add_plugin
from cms.tests.menu import BaseMenuTest

from cms_layouts.models import Layout
from cms_layouts.layout_response import LayoutResponse
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

    def test_next_prev_post(self):
        for i in range(4):
            BlogEntryPage.objects.create(**{
                'title': '%s' % i, 'blog': self.blog,
                'short_description': 'desc', 'is_published': True})
        entries = {e.title: e for e in BlogEntryPage.objects.all()}

        self.assertEquals(entries["0"].previous_post(), None)
        self.assertEquals(entries["0"].next_post().pk, entries["1"].pk)
        self.assertEquals(entries["1"].previous_post().pk, entries["0"].pk)
        self.assertEquals(entries["1"].next_post().pk, entries["2"].pk)
        self.assertEquals(entries["3"].previous_post().pk, entries["2"].pk)
        self.assertEquals(entries["3"].next_post(), None)

    def test_draft(self):
        draft_entry = BlogEntryPage.objects.create(blog=self.blog)
        self.assertTrue(draft_entry.is_draft)
        draft_entry.title = 'Sample title'
        draft_entry.save()
        self.assertTrue(draft_entry.is_draft)
        draft_entry.short_description = 'desc'
        draft_entry.save()
        self.assertFalse(draft_entry.is_draft)

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
        data['start_publication'] = '05/06/2014 11:51 AM +03:00'
        start_date = parser.parse(
            data['start_publication']).astimezone(tz.tzutc())
        response = self.client.post(url, data)
        entry = BlogEntryPage.objects.get(id=entry.id)
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
        blog_layout = Layout.objects.create(**{
            'from_page': page_for_layouts,
            'content_object': self.blog,
            'layout_type': Blog.ALL })
        entry = BlogEntryPage.objects.create(**{
            'title': 'Hello', 'blog': self.blog, 'is_published': True,
            'short_description': 'I am a blog entry',
            'meta_keywords': "article,blog,keyword",})
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
        self.entry_url = reverse('admin:cms_blogger_blogentrypage_change',
            args=(self.entry.pk, ))

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
        new_entry_url = reverse('admin:cms_blogger_blogentrypage_change',
            args=(new_entry.pk, ))
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
