# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: notification.py 35 2008-03-03 17:08:32Z s0undt3ch $
# =============================================================================
#             $URL: http://wikinotification.ufsoft.org/svn/trunk/WikiNotification/notification.py $
# $LastChangedDate: 2008-03-03 17:08:32 +0000 (Mon, 03 Mar 2008) $
#             $Rev: 35 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2006 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

import re
import md5

from trac import __version__
from trac.core import *
from trac.util.text import CRLF
from trac.util.datefmt import to_timestamp
from trac.wiki.model import WikiPage
from trac.versioncontrol.diff import unified_diff
from trac.notification import NotifyEmail
from trac.config import Option, BoolOption

from genshi.template.text import TextTemplate


diff_header = """Index: %(name)s
=========================================================================
--- %(name)s (version: %(oldversion)s)
+++ %(name)s (version: %(version)s)
"""

class WikiNotificationSystem(Component):
    smtp_from = Option(
        'wiki-notification', 'smtp_from', 'trac+wiki@localhost',
        """Sender address to use in notification emails.""")

    from_name = Option(
        'wiki-notification', 'from_name', None,
        """Sender name to use in notification emails.

        Defaults to project name.""")

    smtp_always_cc = Option(
        'wiki-notification', 'smtp_always_cc', '',
        """Email address(es) to always send notifications to.

        Addresses can be seen by all recipients (Cc:).

        Seperate each address by a blank space.""")

    smtp_always_bcc = Option(
        'wiki-notification', 'smtp_always_bcc', '',
        """Email address(es) to always send notifications to.

        Addresses do not appear publicly (Bcc:).

        Seperate each address by a blank space.""")

    use_public_cc = BoolOption(
        'wiki-notification', 'use_public_cc', 'false',
        """Recipients can see email addresses of other CC'ed recipients.

        If this option is disabled(the default),
        recipients are put on BCC.

        (values: 1, on, enabled, true or 0, off, disabled, false)""")

    attach_diff = BoolOption(
        'wiki-notification', 'attach_diff', 'false',
        """Send `diff`'s as an attachment instead of inline in email body.""")

    redirect_time = Option(
        'wiki-notification', 'redirect_time', 5,
        """The default seconds a redirect should take when
        watching/un-watching a wiki page""")

    subject_template = Option(
        'wiki-notification', 'subject_template', '$prefix $page.name $action',
        "A Genshi text template snippet used to get the notification subject.")


class WikiNotifyEmail(NotifyEmail):
    template_name = "wiki_notification_email_template.txt"
    from_email = 'trac+wiki@localhost'
    COLS = 75
    newwiki = False
    wikidiff = None

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
        self.time = time

        self.from_name = self.config.get('wiki-notification', 'from_name')

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

        subject = self.format_subject(action.replace('_', ' '))
        if not self.newwiki:
            subject = 'Re: %s' % subject

        NotifyEmail.notify(self, page.name, subject)

    def get_message_id(self, rcpt, time=None):
        """Generate a predictable, but sufficiently unique message ID."""
        s = '%s.%s.%d.%d.%s' % (self.config.get('project', 'url'),
                                self.page.name, self.page.version,
                                to_timestamp(time),
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
        self.env.log.debug("SID'S TO NOTIFY: %s", sids)
        QUERY_EMAILS = """SELECT value FROM session_attribute
                          WHERE name=%s AND sid=%s"""
        for sid in sids:
            if sid[0] != self.change_author:
                self.env.log.debug('SID: %s', sid[0])
                cursor.execute(QUERY_EMAILS, ('email', sid[0]))
                tos.append(cursor.fetchone()[0])

        self.env.log.debug("TO's TO NOTIFY: %s", tos)
        return (tos, [])

    def send(self, torcpts, ccrcpts, mime_headers={}):
        from email.MIMEText import MIMEText
        from email.Utils import formatdate

        attach_diff = self.config.getbool('wiki-notification', 'attach_diff')
        if attach_diff:
            from email.MIMEMultipart import MIMEMultipart
            self.data["wikidiff"] = None

        stream = self.template.generate(**self.data)
        body = stream.render('text')
        projname = self.config.get('project', 'name')
        public_cc = self.config.getbool('wiki-notification', 'use_public_cc')
        headers = {}
        headers['X-Mailer'] = 'Trac %s, by Edgewall Software' % __version__
        headers['X-Trac-Version'] =  __version__
        headers['X-Trac-Project'] =  projname
        headers['X-URL'] = self.config.get('project', 'url')
        headers['Precedence'] = 'bulk'
        headers['Auto-Submitted'] = 'auto-generated'
        headers['Subject'] = self.subject
        headers['From'] = (self.from_name or projname, self.from_email)
        headers['Reply-To'] = self.replyto_email

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
        accparam = self.config.get('wiki-notification', 'smtp_always_cc')
        accaddrs = accparam and \
                   build_addresses(accparam.replace(',', ' ').split()) or []
        bccparam = self.config.get('wiki-notification', 'smtp_always_bcc')
        bccaddrs = bccparam and \
                   build_addresses(bccparam.replace(',', ' ').split()) or []

        recipients = []
        (toaddrs, recipients) = remove_dup(toaddrs, recipients)
        (ccaddrs, recipients) = remove_dup(ccaddrs, recipients)
        (accaddrs, recipients) = remove_dup(accaddrs, recipients)
        (bccaddrs, recipients) = remove_dup(bccaddrs, recipients)

        # if there is not valid recipient, leave immediately
        if len(recipients) < 1:
            self.env.log.info('no recipient for a wiki notification')
            return

        dest = self.change_author or 'anonymous'
        message_id = self.get_message_id(dest, self.time)
        headers['Message-ID'] = message_id
        headers['X-Trac-Wiki-URL'] = self.data['link']
        if not self.newwiki:
            reply_msgid = self.get_message_id(dest)
            headers['In-Reply-To'] = headers['References'] = reply_msgid

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
                raise TracError(_("WikiPage contains non-Ascii chars. " \
                                  "Please change encoding setting"))

        if attach_diff:
            # With MIMEMultipart the charset has to be set before any parts
            # are added.
            msg = MIMEMultipart()
            del msg['Content-Transfer-Encoding']
            msg.set_charset(self._charset)
            msg.preamble = 'This is a multi-part message in MIME format.'

            # The text Message
            mail = MIMEText(body, 'plain')
            mail.add_header('Content-Disposition', 'inline',
                            filename="message.txt")
            # Re-Setting Content Transfer Encoding
            del mail['Content-Transfer-Encoding']
            mail.set_charset(self._charset)
            msg.attach(mail)
            try:
                # The Diff Attachment
                attach = MIMEText(self.wikidiff.encode('utf-8'), 'x-patch')
                attach.add_header('Content-Disposition', 'inline',
                                  filename=self.page.name + '.diff')
                del attach['Content-Transfer-Encoding']
                attach.set_charset(self._charset)
                msg.attach(attach)
            except AttributeError:
                # We don't have a wikidiff to attach
                pass
        else:
            msg = MIMEText(body, 'plain')
            # Message class computes the wrong type from MIMEText constructor,
            # which does not take a Charset object as initializer. Reset the
            # encoding type to force a new, valid evaluation
            del msg['Content-Transfer-Encoding']
            msg.set_charset(self._charset)

        self.add_headers(msg, headers);
        self.add_headers(msg, mime_headers);
        self.env.log.info("Sending SMTP notification to %s:%d to %s"
                           % (self.smtp_server, self.smtp_port, recipients))
        msgtext = msg.as_string()
        # Ensure the message complies with RFC2822: use CRLF line endings
        recrlf = re.compile("\r?\n")
        msgtext = CRLF.join(recrlf.split(msgtext))
        self.server.sendmail(msg['From'], recipients, msgtext)

    def format_subject(self, action):
        template = self.config.get('wiki-notification', 'subject_template')
        template = TextTemplate(template.encode('utf8'))

        prefix = self.config.get('notification', 'smtp_subject_prefix')
        if prefix == '__default__':
            prefix = '[%s]' % self.config.get('project', 'name')

        data = {
            'page': self.page,
            'prefix': prefix,
            'action': action
        }
        return template.generate(**data).render('text', encoding=None).strip()
