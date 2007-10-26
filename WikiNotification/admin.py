# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: admin.py 24 2007-10-26 15:58:00Z s0undt3ch $
# =============================================================================
#             $URL: http://wikinotification.ufsoft.org/svn/trunk/WikiNotification/admin.py $
# $LastChangedDate: 2007-10-26 16:58:00 +0100 (Fri, 26 Oct 2007) $
#             $Rev: 24 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 Ufsoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

from trac.core import *
from trac.web.chrome import ITemplateProvider
from trac.admin import IAdminPanelProvider
from trac.config import Option, _TRUE_VALUES
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
#            yield ('wikinotification', 'Wiki Notifications',
#                   'users', 'User Notifications')

    def render_admin_panel(self, req, cat, page, path_info):
        if page == 'config':
            return self._do_config(req, cat, page, path_info)
#        elif page == 'users':
#            return self._do_users(req)

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
            if option.name == 'use_public_cc':
                value = self.config.getbool('wiki-notification', option.name,
                                            option.default)
            elif option.name in ('smtp_always_bcc', 'smtp_always_cc'):
                value = self.config.getlist('wiki-notification', option.name,
                                            option.default)
            else:
                value = self.config.get('wiki-notification', option.name,
                                        option.default)
            if value:
                option.value = value
            self.options[option.name] = option

        self._get_extra_config_errors()

        if req.method == 'POST':
            for option in ('redirect_time', 'smtp_always_bcc', 'smtp_always_cc',
                           'smtp_from', 'use_public_cc'):
                if option == 'use_public_cc':
                    self.config.set('wiki-notification', option,
                                    req.args.get(option) in _TRUE_VALUES)
                else:
                    self.config.set('wiki-notification', option,
                                req.args.get(option))
            self.config.save()
            req.redirect(req.href.admin(cat, page))
        return 'admin_config.html', {'wnoptions': self.options}
