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
            ('categories', self.gf('tagging.fields.TagField')(null=True)),
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
        ))
        db.send_create_signal('cms_blogger', ['BlogEntry'])

        # Adding unique constraint on 'BlogEntry', fields ['slug', 'creation_date', 'blog']
        db.create_unique('cms_blogger_blogentry', ['slug', 'creation_date', 'blog_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'BlogEntry', fields ['slug', 'creation_date', 'blog']
        db.delete_unique('cms_blogger_blogentry', ['slug', 'creation_date', 'blog_id'])

        # Removing unique constraint on 'Blog', fields ['slug', 'site']
        db.delete_unique('cms_blogger_blog', ['slug', 'site_id'])

        # Deleting model 'Blog'
        db.delete_table('cms_blogger_blog')

        # Deleting model 'BioPage'
        db.delete_table('cms_blogger_biopage')

        # Deleting model 'BlogEntry'
        db.delete_table('cms_blogger_blogentry')


    models = {
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'cms_blogger.blogentry': {
            'Meta': {'unique_together': "(('slug', 'creation_date', 'blog'),)", 'object_name': 'BlogEntry'},
            'abstract': ('django.db.models.fields.TextField', [], {'max_length': '400', 'blank': 'True'}),
            'author': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'blog': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms_blogger.Blog']"}),
            'content': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'article_entry'", 'null': 'True', 'to': "orm['cms.Placeholder']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'end_publication': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'meta_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'meta_keywords': ('django.db.models.fields.CharField', [], {'max_length': '120', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'start_publication': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '120'})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['cms_blogger']