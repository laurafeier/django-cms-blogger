SITE_ID = 1
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.sitemaps',
    'cms',
    'mptt',
    'menus',
    'south',
    'sekizai',
    'filer',
    'cms.plugins.text',
    # all test apps for cms; these are required only for tests since
    #   we're using cms test utils
    'cms.plugins.picture',
    'cms.plugins.file',
    'cms.plugins.flash',
    'cms.plugins.link',
    'cms.plugins.snippet',
    'cms.plugins.googlemap',
    'cms.plugins.teaser',
    'cms.plugins.video',
    'cms.plugins.twitter',
    'cms.plugins.inherit',
    'cms.test_utils.project.sampleapp',
    'cms.test_utils.project.placeholderapp',
    'cms.test_utils.project.pluginapp',
    'cms.test_utils.project.pluginapp.plugins.manytomany_rel',
    'cms.test_utils.project.pluginapp.plugins.extra_context',
    'cms.test_utils.project.fakemlng',
    'cms.test_utils.project.fileapp',
    'reversion',

    'django_select2',
    'cms_layouts',
    'cms_blogger',
]

CMS_TEMPLATES = [('page_template.html', 'page_template.html'), ]
CMS_MODERATOR = False
CMS_PERMISSION = True
STATIC_ROOT = ''
STATIC_URL = '/static/'
ROOT_URLCONF = 'cms_blogger.tests.urls'

TEMPLATE_CONTEXT_PROCESSORS = [
    "django.contrib.auth.context_processors.auth",
    'django.contrib.messages.context_processors.messages',
    "django.core.context_processors.i18n",
    "django.core.context_processors.debug",
    "django.core.context_processors.request",
    "django.core.context_processors.media",
    'django.core.context_processors.csrf',
    "cms.context_processors.media",
    "sekizai.context_processors.sekizai",
    "django.core.context_processors.static",
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME' : 'test.db', # Or path to database file if using sqlite3.
        'USER' : '', # Not used with sqlite3.
        'PASSWORD' : '', # Not used with sqlite3.
        'HOST' : '', # Set to empty string for localhost. Not used with sqlite3.
        'PORT' : '', # Set to empty string for default. Not used with sqlite3.
    }
}
MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
)

TEMPLATE_LOADERS = (
    'cms_layouts.tests.utils.MockLoader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    )

CACHE_BACKEND = 'locmem:///'

CMS_PLUGIN_PROCESSORS = ('cms_layouts.context_processor.add_extra_html', )
SOUTH_TESTS_MIGRATE = False
BLOGGER_ALLOWED_SITES_FOR_USER =  'cms_blogger.tests.utils.get_allowed_sites'
USE_TZ = True
