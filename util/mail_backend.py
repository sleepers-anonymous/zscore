import logging
import email.MIMEBase

import django.core.mail
import django.core.mail.backends.base


# Modified from BSD 3-clause licensed code copyright (c) Waldemar Kornewald,
# Thomas Wanschik, and others, from
# https://github.com/django-nonrel/djangoappengine/blob/master/djangoappengine/mail.py
class GAEMailBackend(django.core.mail.backends.base.BaseEmailBackend):
    def send_messages(self, email_messages):
        num_sent = 0
        for message in email_messages:
            if self._send(message):
                num_sent += 1
        return num_sent

    def _copy_message(self, message):
        """Creates and returns App Engine EmailMessage class from message."""
        from google.appengine.api import mail
        gae_message = mail.EmailMessage(sender=message.from_email,
                                        to=message.to,
                                        subject=message.subject,
                                        body=message.body)
        reply_to = message.extra_headers.get('Reply-To')
        if reply_to:
            gae_message.reply_to = reply_to
        if message.cc:
            gae_message.cc = list(message.cc)
        if message.bcc:
            gae_message.bcc = list(message.bcc)
        if message.attachments:
            # Must be populated with (filename, filecontents) tuples.
            attachments = []
            for attachment in message.attachments:
                if isinstance(attachment, email.MIMEBase.MIMEBase):
                    attachments.append((attachment.get_filename(),
                                        attachment.get_payload(decode=True)))
                else:
                    attachments.append((attachment[0], attachment[1]))
            gae_message.attachments = attachments
        # Look for HTML alternative content.
        if isinstance(message, django.core.mail.EmailMultiAlternatives):
            for content, mimetype in message.alternatives:
                if mimetype == 'text/html':
                    gae_message.html = content
                    break
        return gae_message

    def _send(self, message):
        try:
            message = self._copy_message(message)
            message.send()
            return True
        except Exception as err:
            logging.warn(err)
            if self.fail_silently:
                return False
            else:
                raise
