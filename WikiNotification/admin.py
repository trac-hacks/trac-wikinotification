# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: admin.py 39 2008-03-04 15:15:49Z s0undt3ch $
# =============================================================================
#             $URL: http://wikinotification.ufsoft.org/svn/trunk/WikiNotification/admin.py $
# $LastChangedDate: 2008-03-04 15:15:49 +0000 (Tue, 04 Mar 2008) $
#             $Rev: 39 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 Ufsoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

from trac.core import *
from trac.web.chrome import ITemplateProvider
from trac.admin import IAdminPanelProvider
from trac.config import Option
from genshi.builder import tag
from genshi.core import Markup

class WikiNotificationAdminPanel(Component):
    implements(ITemplateProvider, IAdminPanelProvider)

    def __init__(self):
        self.options = {}

    # IAdminPanelProvider
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('wikinotification', 'Wiki Notifications',
                   'config', 'Configuration')
            yield ('wikinotification', 'Wiki Notifications',
                   'users', 'User Notifications')

    def render_admin_panel(self, req, cat, page, path_info):
        if page == 'config':
            return self._do_config(req, cat, page, path_info)
        elif page == 'users':
            return self._do_users(req, cat, page, path_info)

    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return []

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        Genshi templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # Internal methods

    def _get_extra_config_errors(self):
        errors = {}
        if not self.config.get('project', 'url', None):
            errors['Project Url'] = "You have not yet defined the project's" + \
            " 'url' setting under the 'project' section on 'trac.ini'."

        if not self.config.get('project', 'admin', None):
            errors['Project Admin'] = "You have not yet defined the " + \
            "project's 'admin' email address setting under the 'project' " + \
            "section on 'trac.ini'"
        self.options['errors'] = errors
        #return errors

    def _do_config(self, req, cat, page, path_info):

        for option in [option for option in Option.registry.values()
                       if option.section == 'wiki-notification']:
            value = ''
            if option.name in ('use_public_cc', 'attach_diff'):
                value = self.config.getbool('wiki-notification', option.name,
                                            option.default)
                if value==True:
                    option.checked = 'checked'
                else:
                    option.checked = None

            elif option.name in ('smtp_always_bcc', 'smtp_always_cc',
                                 'banned_addresses'):
                value = self.config.getlist('wiki-notification', option.name,
                                            option.default)
            else:
                value = self.config.get('wiki-notification', option.name,
                                        option.default)
            if value:
                option.value = value
            option.doc = option.__doc__.split('\n\n')
            self.options[option.name] = option

        self._get_extra_config_errors()

        if req.method == 'POST':
            for option in ('redirect_time', 'smtp_always_bcc', 'smtp_always_cc',
                           'from_email', 'use_public_cc', 'banned_addresses',
                           'attach_diff', 'subject_template', 'from_name'):
                if option in ('use_public_cc', 'attach_diff'):
                    self.config.set('wiki-notification', option,
                                    (req.args.get(option) == 'yes') and \
                                    'true' or 'false')
                else:
                    self.config.set('wiki-notification', option,
                                    req.args.get(option))
            self.config.save()
            req.redirect(req.href.admin(cat, page))
        return 'admin_config.html', {'wnoptions': self.options}

    def _do_users(self, req, cat, page, path_info):
        sql = "SELECT sid,authenticated,value " + \
              "FROM session_attribute WHERE name = 'watched_pages';"
        notified_users = []
        for user, authenticated, pages in self.env.db_query(sql):
            attrs = {}
            attrs['sid'] = user
            attrs['authenticated'] = authenticated
            attrs['pages'] = pages.strip(',').split(',')
            notified_users.append(attrs)

        return 'admin_user_notifications.html', {'wpages': notified_users,
                                                 'wikiurl':req.href.wiki()}
