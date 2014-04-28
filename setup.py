import os
from setuptools import setup, find_packages


README = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md')


DEPENDENCIES = [
    'django >=1.4, <1.5',
    'django-cms>=2.3.5,<2.3.6',
    'django-cms-layouts>=0.1',
    'django-select2',
    'django-filer',
    'python-dateutil >= 2.2',
]

DEPENDENCY_LINKS = [
    'http://github.com/laurafeier/django-cms-layouts/tarball/master#egg=django-cms-layouts-0.1'
]

setup(
    name='django-cms-blogger',
    version='0.1',
    description='Django CMS blogging tool that lets users create blogs '
                'using layouts created from CMS pages.',
    long_description=open(README, 'r').read(),
    author='Laura Feier',
    author_email='feierlaura10@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=DEPENDENCIES,
    dependency_links=DEPENDENCY_LINKS,
    setup_requires=['s3sourceuploader', ],
    classifiers=[]
)
