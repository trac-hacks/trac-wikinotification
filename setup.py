#!/usr/bin/env python

# $Id: setup.py 2 2006-09-28 22:08:17Z s0undt3ch $

from setuptools import setup, find_packages

PACKAGE = 'TracWikiNotification'
VERSION = '0.1.0'
AUTHOR = 'Pedro Algarvio'
AUTHOR_EMAIL = 'ufs@ufsoft.org'
SUMMARY = "Trac Plugin to allow email notification of changes on wiki pages"
DESCRIPTION = """
==============================
 Trac Wiki Notification Plugin
==============================

Trac Wiki Notification is a pluggin that allows users to select the wiki pages
that they wish to be notified(by email) when a change occurs on it.

You can find more info on the
`Trac WikiNotification <http://wikinotification.ufsoft.org/>`_ site where bugs and new
feature requests should go to.

Download and Installation
-------------------------

Trac WikiNotification can be installed with `Easy Install
<http://peak.telecommunity.com/DevCenter/EasyInstall>`_ by typing::

    > easy_install TracWikiNotification

"""
HOME_PAGE = 'http://wikinotification.ufsoft.org'
LICENSE = 'BSD'

setup(name=PACKAGE,
      version=VERSION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=HOME_PAGE,
      download_url='http://python.org/pypi/TracWikiNotification',
      description=SUMMARY,
      long_description=DESCRIPTION,
      license=LICENSE,
      platforms="OS Independent - Anywhere Python and Trac >=0.10 is known to run.",
      install_requires = ['TracCtxtnavAdd'],
      packages=find_packages(),
      package_data={
          'WikiNotification': [
              'templates/*.cs',
          ]
      },
      entry_points = {
          'trac.plugins': [
              'wikinotification = WikiNotification',
          ]
      },
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Web Environment',
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
