# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: notification.py 23 2007-10-25 16:32:10Z s0undt3ch $
# =============================================================================
#             $URL: http://wikinotification.ufsoft.org/svn/trunk/WikiNotification/notification.py $
# $LastChangedDate: 2007-10-25 17:32:10 +0100 (Thu, 25 Oct 2007) $
#             $Rev: 23 $
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

diff_header = """Index: %(name)s
===================================================================
--- %(name)s (version: %(oldversion)s)
+++ %(name)s (version: %(version)s)
"""

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
        """The default seconds a redirect should take when
        watching/un-watching a wiki page""")


class WikiNotifyEmail(NotifyEmail):
    template_name = "notification_email.html"
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

        self.data['name']= page.name
        self.data['text']= page.text
        self.data['version']= version
        self.data['author']= author
        self.data['comment']= comment
        self.data['ip']= ipnr
        self.data['action']= action
        self.data['link']= self.env.abs_href.wiki(page.name)
        self.data['linkdiff']= "%s?action=diff&version=%i" % \
                               (self.env.abs_href.wiki(page.name),
                                page.version)
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

        projname = self.config.get('project', 'name')
        subject = '[%s] Notification: %s %s' % (projname, page.name,
                                                action.replace('_', ' '))

        NotifyEmail.notify(self, page.name, subject)

    def get_message_id(self, rcpt):
        """Generate a predictable, but sufficiently unique message ID."""
        s = '%s.%s.%d.%s' % (self.config.get('project', 'url'),
                               self.page.name, self.page.version,
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

    def send(self, torcpts, ccrcpts, mime_headers={}):
        import re
        from email.MIMEText import MIMEText
        from email.MIMEMultipart import MIMEMultipart
        from email.Utils import formatdate, formataddr
        from trac import __version__
        stream = self.template.generate(**self.data)
        body = stream.render('text')
        projname = self.config.get('project', 'name')
        public_cc = self.config['wiki-notification'].get('smtp_public_cc')

        headers = {}
        headers['X-Mailer'] = 'Trac %s, by Edgewall Software' % __version__
        headers['X-Trac-Version'] =  __version__
        headers['X-Trac-Project'] =  projname
        headers['X-URL'] = self.config.get('project', 'url')
        headers['Subject'] = self.subject
        headers['From'] = (projname, self.from_email)
        headers['Sender'] = self.from_email
        headers['Reply-To'] = self.replyto_email

        always_cc = self.config['wiki-notification'].get('smtp_always_cc')
        always_bcc = self.config['wiki-notification'].get('smtp_always_bcc')
        hdrs = {}
        dest = filter(None, torcpts) or filter(None, ccrcpts) or \
                filter(None, [always_cc]) or filter(None, [always_bcc])
        self.env.log.debug('DEST: %s', dest)
        if not dest:
            self.env.log.info('no recipient for a wiki notification')
            return

        headers['Message-ID'] = self.get_message_id(dest[0])
        headers['X-Trac-Wiki-URL'] = self.env.abs_href.wiki(self.page.name)
        if not self.newwiki:
            headers['In-Reply-To'] = self.get_message_id(dest[0])
            headers['References'] = self.get_message_id(dest[0])

        def build_addresses(rcpts):
            """Format and remove invalid addresses"""
            return filter(lambda x: x, \
                          [self.get_smtp_address(addr) for addr in rcpts])

        def remove_dup(rcpts, all):
            """Remove duplicates"""
            tmp = []
            for rcpt in rcpts:
                if not rcpt in all:
                    tmp.append(rcpt)
                    all.append(rcpt)
            return (tmp, all)

        toaddrs = build_addresses(torcpts)
        ccaddrs = build_addresses(ccrcpts)
        accparam = self.config['wiki-notification'].get('smtp_always_cc')
        accaddrs = accparam and \
                build_addresses(accparam.replace(',', ' ').split()) or []
        bccparam = self.config['wiki-notification'].get('smtp_always_bcc')
        bccaddrs = bccparam and \
                build_addresses(bccparam.replace(',', ' ').split()) or []
        recipients = []
        (toaddrs, recipients) = remove_dup(toaddrs, recipients)
        (ccaddrs, recipients) = remove_dup(ccaddrs, recipients)
        (accaddrs, recipients) = remove_dup(accaddrs, recipients)
        (bccaddrs, recipients) = remove_dup(bccaddrs, recipients)

        # if there is no valid recipient, leave immediately
        if len(recipients) < 1:
            self.env.log.debug("0 recipients, exiting")
            return

        pcc = accaddrs
        if public_cc:
            pcc += ccaddrs
            if toaddrs:
                headers['To'] = ', '.join(toaddrs)
        if pcc:
            headers['Cc'] = ', '.join(pcc)
        headers['Date'] = formatdate()
        # sanity check
        if not self._charset.body_encoding:
            try:
                dummy = body.encode('ascii')
            except UnicodeDecodeError:
                raise TracError, "Ticket contains non-Ascii chars. " \
                        "Please change encoding setting"


        mail = MIMEMultipart()
        # With MIMEMultipart the charset has to be set before any parts
        # are added.
        del mail['Content-Transfer-Encoding']
        mail.set_charset(self._charset)
        mail.preamble = 'This is a multi-part message in MIME format.'

        # The text Message
        msg = MIMEText(body, 'plain')
        msg.add_header('Content-Disposition', 'inline', filename="message")
        # Re-Setting Content Transfer Encoding
        del msg['Content-Transfer-Encoding']
        msg.set_charset(self._charset)
        mail.attach(msg)
        try:
            # The Diff Attachment
            attach = MIMEText(self.wikidiff.encode('utf-8'), 'x-patch')
            attach.add_header('Content-Disposition', 'inline',
                              filename=self.page.name + '.diff')
            del attach['Content-Transfer-Encoding']
            attach.set_charset(self._charset)
            mail.attach(attach)
        except AttributeError:
            # We don't have a wikidiff to attach
            pass

        self.add_headers(mail, headers);
        self.add_headers(mail, mime_headers);

        self.env.log.debug("Sending SMTP notification to %s on port %d to %s"
                           % (self.smtp_server, self.smtp_port, recipients))
        msgtext = mail.as_string()
        # Ensure the message complies with RFC2822: use CRLF line endings
        recrlf = re.compile("\r?\n")
        msgtext = "\r\n".join(recrlf.split(msgtext))
        self.server.sendmail(mail['From'], recipients, msgtext)
