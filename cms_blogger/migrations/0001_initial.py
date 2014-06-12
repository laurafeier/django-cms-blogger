# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'BlogNavigationNode'
        db.create_table('cms_blogger_blognavigationnode', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('position', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('parent_node_id', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('cms_blogger', ['BlogNavigationNode'])

        # Adding model 'Blog'
        db.create_table('cms_blogger_blog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sites.Site'])),
            ('entries_slugs_with_date', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
            ('tagline', self.gf('django.db.models.fields.CharField')(max_length=70, null=True, blank=True)),
            ('branding_image', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['filer.Image'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('in_navigation', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('navigation_node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms_blogger.BlogNavigationNode'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('enable_facebook', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('enable_twitter', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('email_account_link', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('enable_disqus', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('disqus_shortname', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('disable_disqus_for_mobile', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('cms_blogger', ['Blog'])

        # Adding unique constraint on 'Blog', fields ['slug', 'site']
        db.create_unique('cms_blogger_blog', ['slug', 'site_id'])

        # Adding M2M table for field allowed_users on 'Blog'
        db.create_table('cms_blogger_blog_allowed_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('blog', models.ForeignKey(orm['cms_blogger.blog'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('cms_blogger_blog_allowed_users', ['blog_id', 'user_id'])

        # Adding model 'Author'
        db.create_table('cms_blogger_author', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='blog_authors', null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=150)),
        ))
        db.send_create_signal('cms_blogger', ['Author'])

        # Adding model 'BioPage'
        db.create_table('cms_blogger_biopage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms_blogger.Author'])),
            ('blog', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms_blogger.Blog'])),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('cms_blogger', ['BioPage'])

        # Adding model 'BlogEntryPage'
        db.create_table('cms_blogger_blogentrypage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms.Placeholder'], null=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=255)),
            ('publication_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('poster_image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, blank=True)),
            ('caption', self.gf('django.db.models.fields.CharField')(max_length=70, null=True, blank=True)),
            ('credit', self.gf('django.db.models.fields.CharField')(max_length=35, null=True, blank=True)),
            ('short_description', self.gf('django.db.models.fields.TextField')(max_length=400)),
            ('start_publication', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
            ('end_publication', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
            ('is_published', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('seo_title', self.gf('django.db.models.fields.CharField')(max_length=120, blank=True)),
            ('meta_keywords', self.gf('django.db.models.fields.CharField')(max_length=120, blank=True)),
            ('disqus_enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('enable_poster_image', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('draft_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('blog', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms_blogger.Blog'])),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('cms_blogger', ['BlogEntryPage'])

        # Adding unique constraint on 'BlogEntryPage', fields ['slug', 'blog', 'draft_id']
        db.create_unique('cms_blogger_blogentrypage', ['slug', 'blog_id', 'draft_id'])

        # Adding M2M table for field authors on 'BlogEntryPage'
        db.create_table('cms_blogger_blogentrypage_authors', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('blogentrypage', models.ForeignKey(orm['cms_blogger.blogentrypage'], null=False)),
            ('author', models.ForeignKey(orm['cms_blogger.author'], null=False))
        ))
        db.create_unique('cms_blogger_blogentrypage_authors', ['blogentrypage_id', 'author_id'])

        # Adding model 'BlogCategory'
        db.create_table('cms_blogger_blogcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30, db_index=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=30)),
            ('blog', self.gf('django.db.models.fields.related.ForeignKey')(related_name='categories', to=orm['cms_blogger.Blog'])),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('cms_blogger', ['BlogCategory'])

        # Adding unique constraint on 'BlogCategory', fields ['slug', 'blog']
        db.create_unique('cms_blogger_blogcategory', ['slug', 'blog_id'])

        # Adding M2M table for field entries on 'BlogCategory'
        db.create_table('cms_blogger_blogcategory_entries', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('blogcategory', models.ForeignKey(orm['cms_blogger.blogcategory'], null=False)),
            ('blogentrypage', models.ForeignKey(orm['cms_blogger.blogentrypage'], null=False))
        ))
        db.create_unique('cms_blogger_blogcategory_entries', ['blogcategory_id', 'blogentrypage_id'])

        # Adding model 'RiverPlugin'
        db.create_table('cmsplugin_riverplugin', (
            ('cmsplugin_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.CMSPlugin'], unique=True, primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('categories', self.gf('django.db.models.fields.CharField')(max_length=619)),
            ('display_abstract', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('display_thumbnails', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('paginate_entries', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('number_of_entries', self.gf('django.db.models.fields.PositiveIntegerField')(default=10)),
        ))
        db.send_create_signal('cms_blogger', ['RiverPlugin'])


    def backwards(self, orm):
        # Removing unique constraint on 'BlogCategory', fields ['slug', 'blog']
        db.delete_unique('cms_blogger_blogcategory', ['slug', 'blog_id'])

        # Removing unique constraint on 'BlogEntryPage', fields ['slug', 'blog', 'draft_id']
        db.delete_unique('cms_blogger_blogentrypage', ['slug', 'blog_id', 'draft_id'])

        # Removing unique constraint on 'Blog', fields ['slug', 'site']
        db.delete_unique('cms_blogger_blog', ['slug', 'site_id'])

        # Deleting model 'BlogNavigationNode'
        db.delete_table('cms_blogger_blognavigationnode')

        # Deleting model 'Blog'
        db.delete_table('cms_blogger_blog')

        # Removing M2M table for field allowed_users on 'Blog'
        db.delete_table('cms_blogger_blog_allowed_users')

        # Deleting model 'Author'
        db.delete_table('cms_blogger_author')

        # Deleting model 'BioPage'
        db.delete_table('cms_blogger_biopage')

        # Deleting model 'BlogEntryPage'
        db.delete_table('cms_blogger_blogentrypage')

        # Removing M2M table for field authors on 'BlogEntryPage'
        db.delete_table('cms_blogger_blogentrypage_authors')

        # Deleting model 'BlogCategory'
        db.delete_table('cms_blogger_blogcategory')

        # Removing M2M table for field entries on 'BlogCategory'
        db.delete_table('cms_blogger_blogcategory_entries')

        # Deleting model 'RiverPlugin'
        db.delete_table('cmsplugin_riverplugin')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'cms.cmsplugin': {
            'Meta': {'object_name': 'CMSPlugin'},
            'changed_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 6, 12, 0, 0)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.CMSPlugin']", 'null': 'True', 'blank': 'True'}),
            'placeholder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Placeholder']", 'null': 'True'}),
            'plugin_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
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
        'cms_blogger.author': {
            'Meta': {'object_name': 'Author'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '150'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'blog_authors'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['auth.User']"})
        },
        'cms_blogger.biopage': {
            'Meta': {'object_name': 'BioPage'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms_blogger.Author']"}),
            'blog': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms_blogger.Blog']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'cms_blogger.blog': {
            'Meta': {'unique_together': "(('slug', 'site'),)", 'object_name': 'Blog'},
            'allowed_users': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'}),
            'branding_image': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['filer.Image']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'disable_disqus_for_mobile': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'disqus_shortname': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'email_account_link': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_disqus': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enable_facebook': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_twitter': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'entries_slugs_with_date': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_navigation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'navigation_node': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms_blogger.BlogNavigationNode']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'tagline': ('django.db.models.fields.CharField', [], {'max_length': '70', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'cms_blogger.blogcategory': {
            'Meta': {'unique_together': "(('slug', 'blog'),)", 'object_name': 'BlogCategory'},
            'blog': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'categories'", 'to': "orm['cms_blogger.Blog']"}),
            'entries': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'categories'", 'symmetrical': 'False', 'to': "orm['cms_blogger.BlogEntryPage']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '30'})
        },
        'cms_blogger.blogentrypage': {
            'Meta': {'unique_together': "(('slug', 'blog', 'draft_id'),)", 'object_name': 'BlogEntryPage'},
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'blog_entries'", 'symmetrical': 'False', 'to': "orm['cms_blogger.Author']"}),
            'blog': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms_blogger.Blog']"}),
            'caption': ('django.db.models.fields.CharField', [], {'max_length': '70', 'null': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Placeholder']", 'null': 'True'}),
            'credit': ('django.db.models.fields.CharField', [], {'max_length': '35', 'null': 'True', 'blank': 'True'}),
            'disqus_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'draft_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'enable_poster_image': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'end_publication': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'meta_keywords': ('django.db.models.fields.CharField', [], {'max_length': '120', 'blank': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'poster_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'publication_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'seo_title': ('django.db.models.fields.CharField', [], {'max_length': '120', 'blank': 'True'}),
            'short_description': ('django.db.models.fields.TextField', [], {'max_length': '400'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'start_publication': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'cms_blogger.blognavigationnode': {
            'Meta': {'object_name': 'BlogNavigationNode'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'parent_node_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'cms_blogger.riverplugin': {
            'Meta': {'object_name': 'RiverPlugin', 'db_table': "'cmsplugin_riverplugin'", '_ormbases': ['cms.CMSPlugin']},
            'categories': ('django.db.models.fields.CharField', [], {'max_length': '619'}),
            'cmsplugin_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CMSPlugin']", 'unique': 'True', 'primary_key': 'True'}),
            'display_abstract': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'display_thumbnails': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'number_of_entries': ('django.db.models.fields.PositiveIntegerField', [], {'default': '10'}),
            'paginate_entries': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
        'filer.file': {
            'Meta': {'object_name': 'File'},
            '_file_size': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'db_index': 'True', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'folder': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'all_files'", 'null': 'True', 'to': "orm['filer.Folder']"}),
            'has_all_mandatory_data': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'original_filename': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_files'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['auth.User']"}),
            'polymorphic_ctype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'polymorphic_filer.file_set'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'restricted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sha1': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '40', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'uploaded_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'filer.folder': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Folder'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'folder_type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'filer_owned_folders'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['auth.User']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['filer.Folder']"}),
            'restricted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'shared': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'shared'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['sites.Site']"}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'uploaded_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'filer.image': {
            'Meta': {'object_name': 'Image', '_ormbases': ['filer.File']},
            '_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            '_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'author': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'date_taken': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'default_alt_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'default_caption': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'default_credit': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'file_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['filer.File']", 'unique': 'True', 'primary_key': 'True'}),
            'must_always_publish_author_credit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'must_always_publish_copyright': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'subject_location': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '64', 'null': 'True', 'blank': 'True'})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['cms_blogger']
