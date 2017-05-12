from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from flask import render_template
from flask_mail import Message


class CronMail:

    def __init__(self, app, mail):
        self.app = app
        self.mail = mail
        self.messages = []
        scheduler = BackgroundScheduler()
        scheduler.start()
        scheduler.add_job(self.send_messages, trigger=IntervalTrigger(minutes=5))

    def send_messages(self):
        if self.messages:
            with self.app.app_context():
                with self.mail.connect() as conn:
                    for message in self.messages:
                        conn.send(message)

    def send_notif_message(self, notif):
        msg = Message('Update on ' + notif.source_type + ' ' + str(notif.source_id), recipients=[notif.user.email])
        msg.body = notif.to_text() + '\n\nsee it here: ' + notif.link
        options = {
            'notif': notif
        }
        msg.html = render_template('email/notif.html', **options)
        self.messages.append(msg)

    def send_invite_message(self, email, sender):
        msg = Message('Invitation to Tingsmen', recipients=[email])
        msg.body = sender + ' invited you to join Tingsmen\n\nTingsmen is a social network where you can propose any ' \
                            'change to the platform and, supposing the community is ok with it, it will be developed' \
                            '\n\nWanna know more? visit: https://tingsmen.herokuapp.com'
        options = {
            'sender': sender
        }
        msg.html = render_template('email/invite.html', **options)
        self.messages.append(msg)
