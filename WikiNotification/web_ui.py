# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: web_ui.py 40 2008-03-05 13:53:14Z s0undt3ch $
# =============================================================================
#             $URL: http://wikinotification.ufsoft.org/svn/trunk/WikiNotification/web_ui.py $
# $LastChangedDate: 2008-03-05 13:53:14 +0000 (Wed, 05 Mar 2008) $
#             $Rev: 40 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2006 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

import re
from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web import HTTPNotFound, IRequestHandler
from trac.web.api import ITemplateStreamFilter
from trac.config import Option

from pkg_resources import resource_filename
from genshi.builder import tag
from genshi.filters.transform import Transformer

class WikiNotificationWebModule(Component):

    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
               ITemplateStreamFilter)

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
        if self.config.getbool('notification', 'smtp_enabled', False):
            if req.perm.has_permission('WIKI_VIEW'):
                yield('metanav', 'notification',
                      tag.a('My Notifications',
                            title="Wiki Pages Change Notifications",
                            href=req.href.notification()))


    # ITemplateStreamFilter method
    def filter_stream(self, req, method, filename, stream, data):
        #self.log.debug('ITemplateStreamFilter method')
        if filename != 'wiki_view.html':
            #self.log.debug('filter stream not matching "wiki_view.html"')
            return stream
        if not self.config.getbool('notification', 'smtp_enabled', False):
            return stream
        page = page = req.path_info[6:] or 'WikiStart'
        watched = self._get_watched_pages(req)
        if page in watched:
            link = tag.a('Un-Watch Page', title='Un-Watch Page',
                            href=req.href.notification(page))
        else:
            link = tag.a('Watch Page', title='Watch Page',
                            href=req.href.notification(page))
        #self.log.debug('Transforming output...')
        return stream | Transformer(
            '//div[@id="ctxtnav"]/ul/li[@class="last"]'
        ).attr('class',None).after(tag.li(link,class_="last"))


    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'^/notification(?:/(.*))?', req.path_info)
        if match:
            if match.group(1):
                req.args['notification.wikipage'] = match.group(1)
                self.log.debug('NOTIFICATION PAGE: %s',  match.group(1))
            return True

    def process_request(self, req):
        req.perm.require('WIKI_VIEW')

        if 'email' not in req.session:
            data = { 'notification' : {'error':True},
                    'prefs': {'url':req.href.prefs() }}
            return 'notification.html', data, None

        notification = {'wikiurl':req.href.wiki(),
                        'my_not_url':req.href.notification()}
        try:
            notification['redirect_time'] = \
                req.session['watched_pages.redirect_time']
        except KeyError:
            notification['redirect_time'] = self.redirect_time

        wikipage = req.args.get('notification.wikipage', False)
        watched = self._get_watched_pages(req)
#        self.log.debug('WATCHED PAGES XX: %s', watched)
        if watched == ([''] or [u'']):
            watched = []
#        self.log.debug('WATCHED PAGES YY: %s', watched)
        if wikipage:
            if wikipage in watched:
                notification['action']='unwatch'
                self._unwatch_page(req, wikipage)
            else:
                self._watch_page(req, wikipage)
                notification['action']='watch'
            notification['wikipage']= wikipage
            notification['redir']= req.href.wiki(wikipage)
            notification['showlist']= False
            notification['removelist']= [wikipage]
        else:
            if req.method == 'POST' and req.args.get('remove'):
                sel = req.args.get('sel')
                sel = isinstance(sel, list) and sel or [sel]
                for wikipage in sel:
                    self._unwatch_page(req, wikipage)
                notification['redir']= req.href.notification()
                notification['removelist']= sel
                notification['action']='unwatch'
            elif req.method == 'POST' and req.args.get('update'):
                notification['redirect_time'] = \
                    req.session['watched_pages.redirect_time'] = \
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
        self._cleanup_session(req)

    def _unwatch_page(self, req, page):
        watched = self._get_watched_pages(req)
        watched.remove(page)
        req.session['watched_pages'] = ','+','.join(watched)+','
        self._cleanup_session(req)

    def _cleanup_session(self, req):
        try:
            if req.session['watched_pages'] == u',,':
                del(req.session['watched_pages'])
        except:
            pass
        req.session.save()
