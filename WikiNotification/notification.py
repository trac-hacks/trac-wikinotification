# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: notification.py 2 2006-09-28 22:08:17Z s0undt3ch $
# =============================================================================
#             $URL: http://wikinotification.ufsoft.org/svn/trunk/WikiNotification/notification.py $
# $LastChangedDate: 2006-09-28 23:08:17 +0100 (Thu, 28 Sep 2006) $
#             $Rev: 2 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2006 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

import md5

from trac.core import *
from trac.wiki.model import WikiPage
from trac.versioncontrol.diff import unified_diff
from trac.notification import NotifyEmail
from trac.config import Option, BoolOption

class WikiNotificationSystem(Component):
    smtp_from = Option(
        'wiki-notification', 'smtp_from', 'trac+wiki@localhost',
        """Sender address to use in notification emails.""")

    smtp_always_cc = Option(
        'wiki-notification', 'smtp_always_cc', '',
        """Email address(es) to always send notifications to,
        addresses can be see by all recipients (Cc:).""")

    smtp_always_bcc = Option(
        'wiki-notification', 'smtp_always_bcc', '',
        """Email address(es) to always send notifications to,
        addresses do not appear publicly (Bcc:).""")

    use_public_cc = BoolOption(
        'wiki-notification', 'use_public_cc', 'false',
        """Recipients can see email addresses of other CC'ed recipients.

        If this option is disabled(the default),
        recipients are put on BCC.""")

    redirect_time = Option(
        'wiki-notification', 'redirect_time', 5,
        """The default secconds a redirect should take when
        watching/un-watching a wiki page""")


class WikiNotifyEmail(NotifyEmail):
    template_name = "notification_email.cs"
    from_email = 'trac+wiki@localhost'
    COLS = 75
    newwiki = False

    def __init__(self, env):
        NotifyEmail.__init__(self, env)

    def notify(self, action, page,
               version=None,
               time=None,
               comment=None,
               author=None,
               ipnr=None):
        self.page = page
        self.change_author = author
        if action == "added":
            self.newwiki = True

        self.hdf.set_unescaped('name', page.name)
        self.hdf.set_unescaped('text', page.text)
        self.hdf.set_unescaped('version', version)
        self.hdf.set_unescaped('author', author)
        self.hdf.set_unescaped('comment', comment)
        self.hdf.set_unescaped('ip', ipnr)
        self.hdf.set_unescaped('action', action)
        self.hdf.set_unescaped('link', self.env.abs_href.wiki(page.name))
        self.hdf.set_unescaped('linkdiff', "%s?action=diff&version=%i" % \
                               (self.env.abs_href.wiki(page.name),
                                page.version))
        if page.version > 0:
            oldpage = WikiPage(self.env, page.name, page.version - 1)
            self.hdf.set_unescaped("oldversion", oldpage.version)
            self.hdf.set_unescaped("oldtext", oldpage.text)
            diff = ""
            for line in unified_diff(oldpage.text.splitlines(),
                                     page.text.splitlines(), context=3):
                diff = diff + "%s\n" % line
            self.hdf.set_unescaped('diff', diff)

        projname = self.config.get('project', 'name')
        subject = '[%s] Notification: %s %s' % (
            projname, page.name, action.replace('_', ' '))

        NotifyEmail.notify(self, page.name, subject)

    def get_message_id(self, rcpt):
        """Generate a predictable, but sufficiently unique message ID."""
        s = '%s.%s.%d.%s' % (self.config.get('project', 'url'),
                               self.page.name, self.page.time,
                               rcpt.encode('ascii', 'ignore'))
        dig = md5.new(s).hexdigest()
        host = self.from_email[self.from_email.find('@') + 1:]
        msgid = '<%03d.%s@%s>' % (len(s), dig, host)
        return msgid

    def get_recipients(self, pagename):
        if not self.db:
            self.db = self.env.get_db_cnx()
        cursor = self.db.cursor()
        QUERY_SIDS = """SELECT sid from session_attribute
                        WHERE name=%s AND value LIKE %s"""
        tos = []
        cursor.execute(QUERY_SIDS, ('watched_pages', '%,'+pagename+',%'))
        sids = cursor.fetchall()
        self.env.log.debug('SIDS TO NOTIFY: %s', sids)
        QUERY_EMAILS = """SELECT value FROM session_attribute
                          WHERE name=%s AND sid=%s"""
        for sid in sids:
            if sid[0] != self.change_author:
                self.env.log.debug('SID: %s', sid[0])
                cursor.execute(QUERY_EMAILS, ('email', sid[0]))
                tos.append(cursor.fetchone()[0])

        self.env.log.debug('TO\'s TO NOTIFY: %s', tos)
        return (tos, [])

    def send(self, torcpts, ccrcpts):
        always_cc = self.config['wiki-notification'].get('smtp_always_cc')
        always_bcc = self.config['wiki-notification'].get('smtp_always_bcc')
        self.public_cc = self.config['wiki-notification'].get('smtp_public_cc')
        hdrs = {}
        dest = filter(None, torcpts) or filter(None, ccrcpts) or \
                filter(None, [always_cc]) or filter(None, [always_bcc])
        self.env.log.debug('DEST: %s', dest)
        if not dest:
            self.env.log.info('no recipient for a wiki notification')
            return

        hdrs['Message-ID'] = self.get_message_id(dest[0])
        hdrs['X-Trac-Wiki-URL'] = self.env.abs_href.wiki(self.page.name)
        if not self.newwiki:
            hdrs['In-Reply-To'] = self.get_message_id(dest[0])
            hdrs['References'] = self.get_message_id(dest[0])

        NotifyEmail.send(self, torcpts, ccrcpts, hdrs)
