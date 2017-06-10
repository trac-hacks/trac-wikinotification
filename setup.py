#!/usr/bin/env python

# $Id: setup.py 76 2009-03-11 21:10:23Z s0undt3ch $

import re
from setuptools import setup, find_packages

PACKAGE = 'TracWikiNotification'
VERSION = '0.4.3'
AUTHOR = 'Pedro Algarvio'
AUTHOR_EMAIL = 'ufs@ufsoft.org'
SUMMARY = "Trac Plugin to allow email notification of changes on wiki pages"
HOME_PAGE = 'http://wikinotification.ufsoft.org'
LICENSE = 'BSD'

setup(
    name=PACKAGE,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=HOME_PAGE,
    download_url='https://python.org/pypi/TracWikiNotification',
    description=SUMMARY,
    long_description=re.sub(r'(\.\.[\s]*[\w]*::[\s]*[\w+]*\n)+', r'::\n',
                            open('README.rst').read()),
    license=LICENSE,
    platforms="OS Independent - Anywhere Python and Trac >=0.11 runs.",
    install_requires=['Trac'],
    packages=find_packages(),
    package_data={'WikiNotification': ['templates/*.html', 'templates/*.txt']},
    entry_points={
        'trac.plugins': [
            'wikinotification = WikiNotification',
        ]
    },
    keywords="trac plugin wiki notification",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Trac',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Text Processing',
        'Topic :: Utilities',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ]
)
