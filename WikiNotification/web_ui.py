# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: web_ui.py 2 2006-09-28 22:08:17Z s0undt3ch $
# =============================================================================
#             $URL: http://wikinotification.ufsoft.org/svn/trunk/WikiNotification/web_ui.py $
# $LastChangedDate: 2006-09-28 23:08:17 +0100 (Thu, 28 Sep 2006) $
#             $Rev: 2 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2006 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

import re
from trac.core import *
from trac.util.html import html, Markup
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web import HTTPNotFound, IRequestHandler
from trac.config import Option

from ctxtnavadd.api import ICtxtnavAdder
from pkg_resources import resource_filename

class WikiNotificationWebModule(Component):

    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
               ICtxtnavAdder)

    redirect_time = Option('wiki-notification', 'redirect_time', default=5)

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        resource_dir = resource_filename(__name__, 'templates')
        return [resource_dir]

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'notification'

    def get_navigation_items(self, req):
        from trac.web.chrome import add_script
        yield('metanav', 'notification',
              html.A('My Notifications', href=req.href.notification()))

    # ICtxtnavAdder methods
    def match_ctxtnav_add(self, req):
        return len(req.path_info) <= 1 or req.path_info == '/' or \
                req.path_info.startswith('/wiki')

    def get_ctxtnav_adds(self, req):
        page = req.path_info[6:] or 'WikiStart'
        watched = self._get_watched_pages(req)
        if page in watched:
            yield (req.href.notification(page), 'Un-Watch Page')
        else:
            yield (req.href.notification(page), 'Watch Page')


    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'^/notification(?:/(.*))?', req.path_info)
        if match:
            if match.group(1):
                req.args['notification.wikipage'] = match.group(1)
                self.log.debug('NOTIFICATION PAGE: %s',  match.group(1))
            return True

    def process_request(self, req):
        if 'email' not in req.session:
            req.hdf['notification.error'] = True
            req.hdf['settings.url'] = req.href.settings()
            return 'notification.cs', None
        try:
            req.hdf['notification.redirect_time'] = \
                    req.session['watched_pages.redirect_time']
        except KeyError:
            req.hdf['notification.redirect_time'] = self.redirect_time
        wikipage = req.args.get('notification.wikipage', False)
        watched = self._get_watched_pages(req)
        if watched == ['']:
            watched = []
        self.log.debug('WATCHED PAGES: %s', watched)
        req.hdf['notification.wikiurl'] = req.href.wiki()
        req.hdf['notification.my_not_url'] = req.href.notification()
        if wikipage:
            if wikipage in watched:
                req.hdf['notification.action'] = 'unwatch'
                self._unwatch_page(req, wikipage)
            else:
                self._watch_page(req, wikipage)
                req.hdf['notification.action'] = 'watch'
            req.hdf['notification.wikipage'] = wikipage
            req.hdf['notification.redir'] = req.abs_href.wiki(wikipage)
            req.hdf['notification.showlist'] = False
        else:
            if req.method == 'POST' and req.args.get('remove'):
                sel = req.args.get('sel')
                sel = isinstance(sel, list) and sel or [sel]
                for wikipage in sel:
                    self._unwatch_page(req, wikipage)
                req.hdf['notification.redir'] = req.abs_href.notification()
                req.hdf['notification.removelist'] = sel
            elif req.method == 'POST' and req.args.get('update'):
                req.hdf['notification.redirect_time'] = \
                        req.session['watched_pages.redirect_time'] = \
                        req.args.get('redirect_time')
                req.hdf['notification.showlist'] = True
                req.hdf['notification.list'] = watched
            else:
                req.hdf['notification.showlist'] = True
                req.hdf['notification.list'] = watched

        return 'notification.cs', None

    # Internal methods
    def _get_watched_pages(self, req):
        try:
            watched = req.session['watched_pages'].strip(',').split(',')
            self.log.debug('WATCHED PAGES: %s', watched)
            return watched
        except KeyError:
            return []

    def _watch_page(self, req, page):
        watched = self._get_watched_pages(req)
        watched.append(page)
        req.session['watched_pages'] = ','+','.join(watched)+','

    def _unwatch_page(self, req, page):
        watched = self._get_watched_pages(req)
        watched.remove(page)
        req.session['watched_pages'] = ','+','.join(watched)+','
