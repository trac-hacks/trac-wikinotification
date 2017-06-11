# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: notification.py 66 2008-03-14 09:02:03Z s0undt3ch $
# =============================================================================
#             $URL: http://wikinotification.ufsoft.org/svn/trunk/WikiNotification/notification.py $
# $LastChangedDate: 2008-03-14 09:02:03 +0000 (Fri, 14 Mar 2008) $
#             $Rev: 66 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2006 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

import re

from trac import __version__
from trac.core import *
from trac.util.text import CRLF
from trac.wiki.model import WikiPage
from trac.versioncontrol.diff import unified_diff
from trac.notification import Notify, NotifyEmail, NotificationSystem
from trac.config import Option, BoolOption, ListOption, IntOption
from trac.util.translation import _, deactivate, reactivate
from trac.resource import Resource
from trac.perm import PermissionSystem

from genshi.template.text import NewTextTemplate


diff_header = """Index: %(name)s
=========================================================================
--- %(name)s (version: %(oldversion)s)
+++ %(name)s (version: %(version)s)
"""

class WikiNotificationSystem(Component):
    from_email = Option(
        'wiki-notification', 'from_email', 'trac+wiki@localhost',
        """Sender address to use in notification emails.""")

    from_name = Option(
        'wiki-notification', 'from_name', None,
        """Sender name to use in notification emails.

        Defaults to project name.""")

    smtp_always_cc = ListOption(
        'wiki-notification', 'smtp_always_cc', [],
        doc="""Comma separated list of email address(es) to always send
        notifications to.

        Addresses can be seen by all recipients (Cc:).""")

    smtp_always_bcc = ListOption(
        'wiki-notification', 'smtp_always_bcc', [],
        doc="""Comma separated list of email address(es) to always send
        notifications to.

        Addresses do not appear publicly (Bcc:).""")

    use_public_cc = BoolOption(
        'wiki-notification', 'use_public_cc', False,
        """Recipients can see email addresses of other CC'ed recipients.

        If this option is disabled(the default),
        recipients are put on BCC.

        (values: 1, on, enabled, true or 0, off, disabled, false)""")

    attach_diff = BoolOption(
        'wiki-notification', 'attach_diff', False,
        """Send `diff`'s as an attachment instead of inline in email body.""")

    redirect_time = IntOption(
        'wiki-notification', 'redirect_time', 5,
        """The default seconds a redirect should take when
        watching/un-watching a wiki page""")

    subject_template = Option(
        'wiki-notification', 'subject_template', '$prefix $pagename $action',
        "A Genshi text template snippet used to get the notification subject.")

    banned_addresses = ListOption(
        'wiki-notification', 'banned_addresses', [],
        doc="""A comma separated list of email addresses that should never be
        sent a notification email.""")


class WikiNotifyEmail(NotifyEmail):
    template_name = "wiki_notification_email_template.txt"
    COLS = 75
    newwiki = False
    wikidiff = None

    def __init__(self, env):
        super(WikiNotifyEmail, self).__init__(env)

        wns = WikiNotificationSystem(self.env)
        self.from_email = wns.from_email or \
                          self.config.get('notification', 'smtp_from')
        self.from_name = wns.from_name or self.env.project_name
        self.banned_addresses = wns.banned_addresses

    def notify(self, action, page,
               version=None,
               time=None,
               comment=None,
               author=None,
               ipnr=None,
               redirect=False,
               old_name=None):
        self.page = page
        self.change_author = author
        self.time = time
        self.action = action
        self.version = version
        self.redirect = redirect
        self.old_name = old_name
#        self.env.log.debug("Notify Action: %s", action)
#        self.env.log.debug("Page time: %r, %s", time, time)

        if action == "added":
            self.newwiki = True

        self.data['name']= page.name
        self.data['old_name']= old_name
        self.data['redirect']= redirect
        self.data['text']= page.text
        self.data['version']= version
        self.data['author']= author
        self.data['comment']= comment
        self.data['ip']= ipnr
        self.data['action']= action
        self.data['link']= self.env.abs_href.wiki(page.name)
        self.data['linkdiff'] = self.env.abs_href.wiki(page.name, action='diff',
                                                       version=page.version)
        if page.version > 0 and action == 'modified':
            diff = diff_header % {'name': self.page.name,
                                  'version': self.page.version,
                                  'oldversion': self.page.version -1
                                 }
            oldpage = WikiPage(self.env, page.name, page.version - 1)
            self.data["oldversion"]= oldpage.version
            self.data["oldtext"]= oldpage.text
            for line in unified_diff(oldpage.text.splitlines(),
                                     page.text.splitlines(), context=3):
                diff += "%s\n" % line
                self.wikidiff = diff
        self.data["wikidiff"] = self.wikidiff

        self.subject = self.format_subject(action.replace('_', ' '))
        config = self.config['notification']
        if not config.getbool('smtp_enabled'):
            return
        self.replyto_email = config.get('smtp_replyto')
        self.from_email = self.from_email or self.replyto_email
        if not self.from_email and not self.replyto_email:
            message = tag(
                tag.p(_('Unable to send email due to identity crisis.')),
                # convert explicitly to `Fragment` to avoid breaking message
                # when passing `LazyProxy` object to `Fragment`
                tag.p(to_fragment(tag_(
                    "Neither %(from_)s nor %(reply_to)s are specified in the "
                    "configuration.",
                    from_=tag.strong('[notification] smtp_from'),
                    reply_to=tag.strong('[notification] smtp_replyto')))))
            raise TracError(message, _('SMTP Notification Error'))

        Notify.notify(self, page.name)

    def get_recipients(self, pagename):
        QUERY_SIDS = """SELECT sid from session_attribute
                        WHERE name=%s AND value LIKE %s"""

        QUERY_EMAILS = """SELECT value FROM session_attribute
                          WHERE name=%s AND sid=%s"""
        tos = []
        with self.env.db_query as db:
            cursor = db.cursor()
            cursor.execute(QUERY_SIDS, ('watched_pages', '%,'+pagename+',%'))
            sids = cursor.fetchall()
            self.env.log.debug("SID'S TO NOTIFY: %s", sids)
            perm = PermissionSystem(self.env)
            resource = Resource('wiki', pagename)
            for sid in sids:
                if sid[0] != self.change_author and perm.check_permission(action='WIKI_VIEW', username=sid[0], resource=resource):
                    self.env.log.debug('SID: %s', sid[0])
                    cursor.execute(QUERY_EMAILS, ('email', sid[0]))
                    sid_email = cursor.fetchone()
                    if sid_email is not None:
                        tos.append(sid_email[0])

        self.env.log.debug("TO's TO NOTIFY: %s", tos)
        return (tos, [])

    def send(self, torcpts, ccrcpts, mime_headers={}):
        from email.MIMEText import MIMEText
        from email.Utils import formatdate

        attach_diff = self.config.getbool('wiki-notification', 'attach_diff')
        if attach_diff:
            from email.MIMEMultipart import MIMEMultipart
            self.data["wikidiff"] = None

        charset = str(self._charset)

        stream = self.template.generate(**self.data)
        # don't translate the e-mail stream
        t = deactivate()
        try:
            body = stream.render('text', encoding=charset)
        finally:
            reactivate(t)
#        self.env.log.debug('Email Contents: %s', body)
        public_cc = self.config.getbool('wiki-notification', 'use_public_cc')
        headers = {}
        headers['X-Mailer'] = 'Trac %s, by Edgewall Software' % __version__
        headers['X-Trac-Version'] =  __version__
        headers['X-Trac-Project'] =  self.env.project_name
        headers['X-URL'] = self.env.project_url
        headers['Precedence'] = 'bulk'
        headers['Auto-Submitted'] = 'auto-generated'
        headers['Subject'] = self.subject
        headers['From'] = (self.from_name, self.from_email) if self.from_name else self.from_email
        headers['Reply-To'] = self.replyto_email

        def build_addresses(rcpts):
            """Format and remove invalid addresses"""
            return filter(lambda x: x, \
                          [self.get_smtp_address(addr) for addr in rcpts])

        blocked_addresses = []
        def remove_dup(rcpts, all):
            """Remove duplicates"""
            tmp = []
            for rcpt in rcpts:
                if rcpt in self.banned_addresses:
                    self.env.log.debug("Banned Address: %s", rcpt)
                    blocked_addresses.append(rcpt)
                elif not rcpt in all:
                    tmp.append(rcpt)
                    all.append(rcpt)
            return (tmp, all)

        toaddrs = build_addresses(torcpts)
        ccaddrs = build_addresses(ccrcpts)
        accaddrs = build_addresses(self.config.getlist('wiki-notification', 'smtp_always_cc', []))
        bccaddrs = build_addresses(self.config.getlist('wiki-notification', 'smtp_always_bcc', []))

        recipients = []
        (toaddrs, recipients) = remove_dup(toaddrs, recipients)
        (ccaddrs, recipients) = remove_dup(ccaddrs, recipients)
        (accaddrs, recipients) = remove_dup(accaddrs, recipients)
        (bccaddrs, recipients) = remove_dup(bccaddrs, recipients)

        self.env.log.debug("Not notifying the following addresses: %s",
                           ', '.join(blocked_addresses))

        # if there is not valid recipient, leave immediately
        if len(recipients) < 1:
            self.env.log.info('no recipient for a wiki notification')
            return

        dest = self.change_author or 'anonymous'
        headers['X-Trac-Wiki-URL'] = self.data['link']

        pcc = accaddrs
        if public_cc:
            pcc += ccaddrs
            if toaddrs:
                headers['To'] = ', '.join(toaddrs)
        if pcc:
            headers['Cc'] = ', '.join(pcc)
        headers['Date'] = formatdate()
        if attach_diff:
            # With MIMEMultipart the charset has to be set before any parts
            # are added.
            msg = MIMEMultipart('mixed', None, [], charset=charset)
            msg.preamble = 'This is a multi-part message in MIME format.'

            # The text Message
            mail = MIMEText(body, 'plain', charset)
            mail.add_header('Content-Disposition', 'inline',
                            filename="message.txt")
            msg.attach(mail)
            try:
                # The Diff Attachment
                attach = MIMEText(self.wikidiff.encode('utf-8'), 'x-patch', charset)
                attach.add_header('Content-Disposition', 'inline',
                                  filename=self.page.name + '.diff')
                msg.attach(attach)
            except AttributeError:
                # We don't have a wikidiff to attach
                pass
        else:
            msg = MIMEText(body, 'plain', charset)

        self.add_headers(msg, headers);
        self.add_headers(msg, mime_headers);
        self.env.log.info("Sending notification to %s" % (recipients,))
        try:
            NotificationSystem(self.env).send_email(self.from_email, recipients, msg.as_string())
        except Exception, err:
            self.env.log.debug('Notification could not be sent: %r', err)

    def format_subject(self, action):
        template = self.config.get('wiki-notification', 'subject_template')
        template = NewTextTemplate(template.encode('utf8'))

        prefix = self.config.get('notification', 'smtp_subject_prefix')
        if prefix == '__default__':
            prefix = '[%s]' % self.config.get('project', 'name')

        data = {
            'pagename': self.old_name or self.page.name,
            'prefix': prefix,
            'action': action,
            'env': self.env,
        }
        return template.generate(**data).render('text', encoding=None).strip()
