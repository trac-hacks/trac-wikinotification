#!/usr/bin/env python

# $Id: setup.py 21 2007-10-23 18:52:51Z s0undt3ch $

from setuptools import setup, find_packages

PACKAGE = 'TracWikiNotification'
VERSION = '0.1.1'
AUTHOR = 'Pedro Algarvio'
AUTHOR_EMAIL = 'ufs@ufsoft.org'
SUMMARY = "Trac Plugin to allow email notification of changes on wiki pages"
DESCRIPTION = """
==============================
 Trac Wiki Notification Plugin
==============================

Trac Wiki Notification is a pluggin that allows users(even anonymous,
as long as email is set) to select the wiki pages that they wish to
be notified(by email) when a change occurs on it.

You can find more info on the
`Trac WikiNotification <http://wikinotification.ufsoft.org/>`_ site where bugs and new
feature requests should go to.



Enabling the Plugin
-------------------
It's as simple as::

   [componentes]
   wikinotification.* = enabled



Available Config Options
------------------------
These are the options available to include on your *trac.ini*.

=====================  ====================  ================================
 **Config Setting**     **Default Value**     **Explanation**
---------------------  --------------------  --------------------------------
*redirect_time*        5 (in secconds)       The default secconds a redirect should take when
                                             watching/un-watching a wiki page.
                                             This value is also definable per user, ie, user
                                             is able to configure this, of course for himself.
---------------------  --------------------  --------------------------------
*smtp_always_bcc*      *empty*               Email address(es) to always send notifications to,
                                             addresses do not appear publicly (Bcc:).
---------------------  --------------------  --------------------------------
*smtp_always_cc*       *empty*               Email address(es) to always send notifications to,
                                             addresses can be see by all recipients (Cc:).
---------------------  --------------------  --------------------------------
*smtp_from*            trac.wiki\@localhost  Sender address to use in notification emails.
---------------------  --------------------  --------------------------------
*use_public_cc*        False                 Recipients can see email addresses of other
                                             CC'ed recipients. If this option is
                                             disabled(the default), recipients are put on BCC.
=====================  ====================  ================================



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
              'templates/*.html',
          ]
      },
      entry_points = {
          'trac.plugins': [
              'wikinotification = WikiNotification',
          ]
      },
      classifiers=[
          'Development Status :: 4 - Beta',
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
