==============================
 Trac Wiki Notification Plugin
==============================

Trac WikiNotification_ is a plugin that allows users(even anonymous,
as long as email is set) to select the wiki pages that they wish to
be notified(by email) when a change occurs on it.

**Note**: The user updating the wiki page won't be notified about his own
changes.

You can find more info on the trac WikiNotification_ site where bugs and new
feature requests should go to.

Enabling the Plugin
-------------------
It's as simple as:

.. sourcecode:: ini

   [components]
   wikinotification.* = enabled


Available Configuration Options
-------------------------------
These are the options available to include on your ``trac.ini`` under
``wiki-notification``.

=====================  ==========================  ==========================
 **Config Setting**     **Default Value**          **Explanation**
---------------------  --------------------------  --------------------------
*redirect_time*        5 (in seconds)              The default seconds a
                                                   redirect should take when
                                                   watching/un-watching a
                                                   wiki page.
                                                   This value is also
                                                   definable per user, ie,
                                                   user is able to configure
                                                   this, of course for
                                                   himself.
---------------------  --------------------------  --------------------------
*smtp_always_bcc*      *empty*                     Comma separated list of
                                                   email address(es) to
                                                   always send notifications
                                                   to, addresses do not
                                                   appear publicly (Bcc:).
---------------------  --------------------------  --------------------------
*smtp_always_cc*       *empty*                     Comma separated list of
                                                   email address(es) to
                                                   always send notifications
                                                   to, addresses can be seen
                                                   by all recipients (Cc:).
---------------------  --------------------------  --------------------------
*smtp_from*            trac.wiki\@localhost        Sender address to use in
                                                   notification emails.
---------------------  --------------------------  --------------------------
*from_name*            None                        Sender name to use in
                                                   notification emails.
                                                   Defaults to project name.
---------------------  --------------------------  --------------------------
*use_public_cc*        False                       Recipients can see email
                                                   addresses of other CC'ed
                                                   recipients. If this option
                                                   is disabled(the default),
                                                   recipients are put on BCC.
---------------------  --------------------------  --------------------------
*attach_diff*          False                       Send changes diff as an
                                                   attachment instead of on
                                                   the email text body.
---------------------  --------------------------  --------------------------
*subject_template*     $prefix $page.name $action  A Genshi text template
                                                   snippet used to get the
                                                   notification subject.
---------------------  --------------------------  --------------------------
*banned_addresses*     *empty*                     Comma separated list of
                                                   email addresses to never
                                                   send notifications to.
=====================  ==========================  ==========================

If you want to override these settings then you can include it like the
following example:

.. sourcecode:: ini

   [wiki-notification]
   redirect_time = 5
   smtp_always_bcc = someone@somedomain, another.one@somedomain
   smtp_always_cc = someone.else@somedomain
   smtp_from = trac.wiki@localhost
   from_name = Custom Name
   use_public_cc = false
   attach_diff = true
   subject_template = Foo $prefix $page.name $action
   banned_addresses = banned.user1@somedomain, banned.user2@somedomain


**Note**: For an up-to-date version of this info please `read this`_.


Download and Installation
-------------------------

Trac WikiNotification_ can be installed with `Easy Install`_ by typing:

.. sourcecode:: sh

   > sudo easy_install TracWikiNotification

To install the development version:

.. sourcecode:: sh

   > sudo easy_install http://wikinotification.ufsoft.org/svn/trunk


Trac 0.11 support And Latest WikiNotification Release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As of time of this writing (Mar 3 2008), trac>=0.11 only is supported.
You won't need ``ctxnavadd``, aka, ``TracCtxtnavAdd`` no more.

Aditional Notes(from user input)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``easy_install`` is run from the command line (on Linux) not from within
  Python.


* After installing any plugin for Trac you'll need to restart Apache to see
  it (not all changes to trac.ini require a restart but adding a plugin does).


* Make sure to add the new plugin to ``trac.ini`` :

  .. sourcecode:: ini

    [components]
    wikinotification.* = enabled


* Also should be noted that the ``trac.ini`` configuration for the wiki
  notification should look something like:

  .. sourcecode:: ini

    [wiki-notification]
    smtp_always_cc = someone@somedomain
    smtp_from = trac.wiki@localhost


* **Another note**: a user will never get a notice of his/her own wiki
  modification (which is a little tricky when testing the plugin :))

Tweaking/Customizing The Notification Email Template
----------------------------------------------------
You can, if you wish, tweak the notification email template sent to your users.

Copy the ``wiki_notification_email_template.txt`` file to your trac environment
``templates/`` sub-directory and tweak it to your needs.

Make sure you read the `Genshi Text Templates`_ documentation to see if you don't
break any of the logic in that template.


.. _read this: http://wikinotification.ufsoft.org/browser/trunk/README
.. _Easy Install: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _WikiNotification: http://wikinotification.ufsoft.org
.. _Genshi Text Templates: http://genshi.edgewall.org/wiki/Documentation/0.4.x/text-templates.html
