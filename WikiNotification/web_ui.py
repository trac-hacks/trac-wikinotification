# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: web_ui.py 21 2007-10-23 18:52:51Z s0undt3ch $
# =============================================================================
#             $URL: http://wikinotification.ufsoft.org/svn/trunk/WikiNotification/web_ui.py $
# $LastChangedDate: 2007-10-23 19:52:51 +0100 (Tue, 23 Oct 2007) $
#             $Rev: 21 $
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
            data = { 'notification' : {'error':True},
                    'prefs': {'url':req.href.prefs() }}
            return 'notification.html', data, None

        notification = { 'wikiurl':req.href.wiki(),'my_not_url':req.href.notification(), }
        try:
            notification['redirect_time'] = req.session['watched_pages.redirect_time']
        except KeyError:
            notification['redirect_time'] = self.redirect_time

        wikipage = req.args.get('notification.wikipage', False)
        watched = self._get_watched_pages(req)
        if watched == ['']:
            watched = []
        # self.log.debug('WATCHED PAGES: %s', watched)
        if wikipage:
            if wikipage in watched:
                notification['action']='unwatch'
                self._unwatch_page(req, wikipage)
            else:
                self._watch_page(req, wikipage)
                notification['action']='watch'
            notification['wikipage']= wikipage
            notification['redir']= req.abs_href.wiki(wikipage)
            notification['showlist']= False
            notification['removelist']= [wikipage]
        else:
            if req.method == 'POST' and req.args.get('remove'):
                sel = req.args.get('sel')
                sel = isinstance(sel, list) and sel or [sel]
                for wikipage in sel:
                    self._unwatch_page(req, wikipage)
                notification['redir']= req.abs_href.notification()
                notification['removelist']= sel
            elif req.method == 'POST' and req.args.get('update'):
                notification['redirect_time'] = req.session['watched_pages.redirect_time'] = \
                    req.args.get('redirect_time')
                notification['showlist']= True
                notification['list']= watched
            else:
                notification['showlist']= True
                notification['list']= watched

        return 'notification.html', {'notification':notification}, None

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
