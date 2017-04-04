from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


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
