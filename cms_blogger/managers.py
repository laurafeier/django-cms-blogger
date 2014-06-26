from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Q
from django.utils import timezone


class EntriesQuerysetMixin(object):

    def on_site(self, site=None):
        if not site:
            try:
                site = Site.objects.get_current()
            except Site.DoesNotExist:
                site = None
        return self.filter(blog__site=site)

    def published(self):
        now = timezone.now()
        pub_conditions = Q(
            Q(is_published=True) &
            Q(Q(start_publication__lt=now) |
              Q(start_publication__isnull=True)) &
            Q(Q(end_publication__gte=now) |
              Q(end_publication__isnull=True))
        )
        return self.filter(pub_conditions)

    def unpublished(self):
        return self.filter(is_published=False)


class EmptyEntriesQueryset(models.query.EmptyQuerySet, EntriesQuerysetMixin):
    pass


class EntriesQueryset(models.query.QuerySet, EntriesQuerysetMixin):

    def delete(self):
        # deletes all poster images from the storage
        files_to_delete = list(self.values_list('poster_image', flat=True))
        super(EntriesQueryset, self).delete()
        storage = self.model._meta.get_field('poster_image').storage
        for file_name in filter(lambda x: x, files_to_delete):
            storage.delete(file_name)

    delete.alters_data = True


class EntriesManager(models.Manager):

    def get_empty_query_set(self):
        return EmptyEntriesQueryset(self.model, using=self._db)

    def get_query_set(self):
        return EntriesQueryset(self.model, using=self._db)

    #######################
    # PROXIES TO QUERYSET #
    #######################

    def on_site(self, site=None):
        return self.get_query_set().on_site(site=site)

    def published(self):
        return self.get_query_set().published()

    def unpublished(self):
        return self.get_query_set().unpublished()
