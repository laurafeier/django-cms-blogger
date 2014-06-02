# -*- coding: utf-8 -*-
from django.template.context import RequestContext
from django.contrib.sites.models import Site
from menus.base import NavigationNode, Modifier
from menus.menu_pool import menu_pool
from .models import BlogNavigationNode
from collections import OrderedDict
from itertools import ifilter
from django.core.urlresolvers import reverse
from django.conf import settings


def _make_navigation_node(blog_node, parent, proxy_prefix, visible=None):
    nav_node = NavigationNode(
        blog_node.text,
        "%s%s" % (proxy_prefix, blog_node.get_absolute_url()),
        blog_node.id * -1,
        attr={'blogNode': True},
        visible=visible or blog_node.is_visible())
    if parent:
        nav_node.parent_id = parent.id
        nav_node.parent = parent
        nav_node.parent_namespace = parent.parent_namespace
    return nav_node


class BlogNavigationExtender(Modifier):

    def _blog_node_visibility(self, request):
        # blog nodes should always be visible in the admin
        if ('django.contrib.admin' in settings.INSTALLED_APPS and
                request.path.startswith(reverse('admin:index'))):
            return True
        return False

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        if post_cut:
            return nodes

        proxy_prefix = RequestContext(request).get('PROXY_REWRITE_RULE', '')
        node_visible = self._blog_node_visibility(request)

        # modification date is required here for the following case:
        #   blog A with nav node A has position 0 and parent page A
        #   if another blog node B is added before nav node A, it will have
        #   the same parent page and position as nav node A(since we are not
        #   repositioning all nodes at save time)
        #   In order to preserve the order of the nodes even if they have the
        #   same position in the menu we are relying on the fact that they
        #   will get inserted in the menu in the order of their modification
        #   date(from the oldest node to the newest node)
        blog_nodes = BlogNavigationNode.objects.filter(
            blog__site=Site.objects.get_current()).order_by('modified_at')

        if not node_visible:
            blog_nodes = blog_nodes.filter(blog__in_navigation=True)

        # save all new added nodes in order to mark the selected one
        new_nodes = []
        # user ordered dict in order to insert nodes in the order of their
        #   modification date
        parents_with_children = OrderedDict()
        for blog_node in blog_nodes:
            parent_id = blog_node.parent_node_id
            child = blog_node
            if parent_id not in parents_with_children:
                parents_with_children[parent_id] = []
            parents_with_children[parent_id].append(child)

        # root blog nav nodes are a pecial case since they need to be inserted
        #   in the nodes list not in children list of some parent node
        root_blog_nodes = parents_with_children.pop(None, [])

        # add all nodes that have a page parent
        for b_id in parents_with_children.keys():
            page_node = next(ifilter(lambda n: n.id == b_id, nodes), None)
            if not page_node:
                continue

            for blog_node in parents_with_children.pop(page_node.id):
                blog_nav_node = _make_navigation_node(
                    blog_node, page_node, proxy_prefix, node_visible)
                page_node.children.insert(blog_node.position, blog_nav_node)
                new_nodes.append(blog_nav_node)

        # add all nodes that are on the root level
        if root_blog_nodes:
            # root nodes need to be inserted in the nodes list
            # blog nodes positions are specified related to the visible page
            #   nodes. The blog node needs to be inserted before the visible
            #   page node position in the nodes list.

            nodes_with_position = {
                node: position for position, node in enumerate(nodes)}

            visible_roots =  dict(enumerate((
                node for node in nodes if node.visible and not node.parent)))
            last_node = visible_roots.get(len(visible_roots) - 1)

            for root_blog_node in root_blog_nodes:
                blog_nav_node = _make_navigation_node(
                    root_blog_node, None, proxy_prefix, node_visible)
                # set default position
                position_in_nodes = root_blog_node.position
                # try to find the 'real' position in navigation node list
                root_page = visible_roots.get(root_blog_node.position)
                if root_page:
                    # insert at exact position
                    position_in_nodes = nodes_with_position[root_page]
                elif last_node:
                    # insert after last visible
                    position_in_nodes = nodes_with_position[last_node] + 1

                nodes.insert(position_in_nodes, blog_nav_node)
                new_nodes.append(blog_nav_node)

        # add all blog nodes that are children of other blog nodes
        for b_id in parents_with_children.keys():
            parent_blog_node = next(
                ifilter(lambda n: n.id == b_id, new_nodes), None)
            if not parent_blog_node:
                continue

            for blog_node in parents_with_children.pop(parent_blog_node.id):
                blog_nav_node = _make_navigation_node(
                    blog_node, parent_blog_node, proxy_prefix, node_visible)
                parent_blog_node.children.insert(
                    blog_node.position, blog_nav_node)
                new_nodes.append(blog_nav_node)

        menu_pool._mark_selected(request, new_nodes)
        return nodes


menu_pool.register_modifier(BlogNavigationExtender)
