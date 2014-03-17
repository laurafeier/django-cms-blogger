# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Blog'
        db.create_table('cms_blogger_blog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sites.Site'])),
            ('entries_slugs_with_date', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('categories', self.gf('tagging.fields.TagField')(null=True)),
            ('enable_facebook', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('enable_twitter', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('enable_disqus', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('disqus_shortname', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('disable_disqus_for_mobile', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('cms_blogger', ['Blog'])

        # Adding unique constraint on 'Blog', fields ['slug', 'site']
        db.create_unique('cms_blogger_blog', ['slug', 'site_id'])

        # Adding model 'BioPage'
        db.create_table('cms_blogger_biopage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('blog', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms_blogger.Blog'])),
            ('author_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('cms_blogger', ['BioPage'])

        # Adding model 'BlogEntry'
        db.create_table('cms_blogger_blogentry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('blog', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms_blogger.Blog'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=120)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=255)),
            ('creation_date', self.gf('django.db.models.fields.DateField')(default=datetime.datetime.now, db_index=True)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('abstract', self.gf('django.db.models.fields.TextField')(max_length=400, blank=True)),
            ('content', self.gf('django.db.models.fields.related.ForeignKey')(related_name='article_entry', null=True, to=orm['cms.Placeholder'])),
            ('start_publication', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
            ('end_publication', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
            ('is_published', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('meta_description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('meta_keywords', self.gf('django.db.models.fields.CharField')(max_length=120, blank=True)),
            ('draft_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('cms_blogger', ['BlogEntry'])

        # Adding unique constraint on 'BlogEntry', fields ['slug', 'blog', 'draft_id']
        db.create_unique('cms_blogger_blogentry', ['slug', 'blog_id', 'draft_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'BlogEntry', fields ['slug', 'blog', 'draft_id']
        db.delete_unique('cms_blogger_blogentry', ['slug', 'blog_id', 'draft_id'])

        # Removing unique constraint on 'Blog', fields ['slug', 'site']
        db.delete_unique('cms_blogger_blog', ['slug', 'site_id'])

        # Deleting model 'Blog'
        db.delete_table('cms_blogger_blog')

        # Deleting model 'BioPage'
        db.delete_table('cms_blogger_biopage')

        # Deleting model 'BlogEntry'
        db.delete_table('cms_blogger_blogentry')


    models = {
        'cms.page': {
            'Meta': {'ordering': "('site', 'tree_id', 'lft')", 'object_name': 'Page'},
            'changed_by': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'changed_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_navigation': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'limit_visibility_in_menu': ('django.db.models.fields.SmallIntegerField', [], {'default': 'None', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'moderator_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '1', 'blank': 'True'}),
            'navigation_extenders': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['cms.Page']"}),
            'placeholders': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cms.Placeholder']", 'symmetrical': 'False'}),
            'publication_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'publication_end_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'publisher_is_draft': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'publisher_public': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'publisher_draft'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.Page']"}),
            'publisher_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'reverse_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'soft_root': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.placeholder': {
            'Meta': {'object_name': 'Placeholder'},
            'default_width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slot': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'cms_blogger.biopage': {
            'Meta': {'object_name': 'BioPage'},
            'author_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'blog': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms_blogger.Blog']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'cms_blogger.blog': {
            'Meta': {'unique_together': "(('slug', 'site'),)", 'object_name': 'Blog'},
            'categories': ('tagging.fields.TagField', [], {'null': 'True'}),
            'disable_disqus_for_mobile': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'disqus_shortname': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'enable_disqus': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_facebook': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_twitter': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'entries_slugs_with_date': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'cms_blogger.blogentry': {
            'Meta': {'unique_together': "(('slug', 'blog', 'draft_id'),)", 'object_name': 'BlogEntry'},
            'abstract': ('django.db.models.fields.TextField', [], {'max_length': '400', 'blank': 'True'}),
            'author': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'blog': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms_blogger.Blog']"}),
            'content': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'article_entry'", 'null': 'True', 'to': "orm['cms.Placeholder']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'draft_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'end_publication': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'meta_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'meta_keywords': ('django.db.models.fields.CharField', [], {'max_length': '120', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'start_publication': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '120'})
        },
        'cms_layouts.layout': {
            'Meta': {'object_name': 'Layout'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'from_page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Page']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layout_type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['cms_blogger']