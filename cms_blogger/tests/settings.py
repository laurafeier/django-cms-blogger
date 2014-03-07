DEBUG = True
TEMPLATE_DEBUG = DEBUG

ROOT_URLCONF = 'cms_blogger.tests.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'cms_blogger',
    # Uncomment the next line if you define models in tests/models.py
    # 'cms_blogger.tests',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

STATIC_ROOT = ''
STATIC_URL = '/static/'

SECRET_KEY = 'c8syx=b9zy)+v$07wb+f!=&amp;#38w829lp*r$$%6i_6b@khg1-n5'
