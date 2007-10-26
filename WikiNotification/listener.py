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

    # Internal Methods
    def _get_req(self):
        """Grab req from inspect.stack()"""
        for x in inspect.stack():
            if 'req' in x[0].f_locals:
                self.env.log.debug(x[0].f_locals['req'])
                return x[0].f_locals['req']

    # IWikiChangeListener methods
    def wiki_page_added(self, page):
        version, time, author, comment, ipnr = page.get_history().next()
        wne = WikiNotifyEmail(page.env)
        wne.notify("added", page, version, time, comment, author, ipnr)

    def wiki_page_changed(self, page, version, time, comment, author, ipnr):
        wne = WikiNotifyEmail(page.env)
        wne.notify("modified", page, version, time, comment, author, ipnr)

    def wiki_page_deleted(self, page):
        req = self._get_req()
        ipnr = req.remote_addr
        author = req.authname
        wne = WikiNotifyEmail(page.env)
        wne.notify("deleted", page, ipnr=ipnr, author=author)

    def wiki_page_version_deleted(self, page):
        req = self._get_req()
        ipnr = req.remote_addr
        author = req.authname
        version, time, author, comment, ipnr = page.get_history().next()
        wne = WikiNotifyEmail(page.env)
        wne.notify("deleted_version", page, version=version+1, author=author, ipnr=ipnr)
