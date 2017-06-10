# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: listener.py 24 2007-10-26 15:58:00Z s0undt3ch $
# =============================================================================
#             $URL: http://wikinotification.ufsoft.org/svn/trunk/WikiNotification/listener.py $
# $LastChangedDate: 2007-10-26 16:58:00 +0100 (Fri, 26 Oct 2007) $
#             $Rev: 24 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2006 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

import inspect
from trac.core import *
from trac.wiki.api import IWikiChangeListener

from WikiNotification.notification import WikiNotifyEmail

class WikiNotificationChangeListener(Component):
    """Class that listens for wiki changes."""
    implements(IWikiChangeListener)

    def __init__(self, *args, **kwargs):
        super(Component, self).__init__(*args, **kwargs)

    # Internal Methods
    def _get_req(self):
        """Grab req from the stack"""
        frame = inspect.currentframe()
        try:
            while frame.f_back:
                frame = frame.f_back
                request = frame.f_locals.get('req')
                if request:
                    self.env.log.debug(request)
                    return request
        finally:
            del frame
        return None

    # IWikiChangeListener methods
    def wiki_page_added(self, page):
        version, time, author, comment, ipnr = page.get_history().next()
        wne = WikiNotifyEmail(page.env)
        wne.notify("added", page, version, time, comment, author, ipnr)

    def wiki_page_changed(self, page, version, time, comment, author, ipnr=None):
        wne = WikiNotifyEmail(page.env)
        wne.notify("modified", page, version, time, comment, author, ipnr)

    def wiki_page_deleted(self, page):
        req = self._get_req()
        ipnr = req and req.remote_addr or '127.0.0.1'
        author = req and req.authname or 'trac'
        wne = WikiNotifyEmail(page.env)
        wne.notify("deleted", page, ipnr=ipnr, author=author)

    def wiki_page_version_deleted(self, page):
        version, time, author, comment, ipnr = page.get_history().next()
        wne = WikiNotifyEmail(page.env)
        wne.notify("deleted_version", page, version=version+1, author=author, ipnr=ipnr)

    def wiki_page_renamed(self, page, old_name):
        req = self._get_req()
        ipnr = req and req.remote_addr or '127.0.0.1'
        author = req and req.authname or 'trac'
        redirect = req and req.args.get('redirect') or None
        self._watch_renamed_page(page.name, old_name)
        wne = WikiNotifyEmail(page.env)
        wne.notify("renamed", page, author=author, ipnr=ipnr, redirect=redirect, old_name=old_name)

    def _watch_renamed_page(self, pagename, old_pagename):
        with self.env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("UPDATE session_attribute SET value=value || %s WHERE name=%s AND value LIKE %s AND value NOT LIKE %s", ('%s,' % pagename, 'watched_pages', '%,' + old_pagename + ',%', '%,' + pagename + ',%'))
