from app import db


class MailingList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<MailingList %r>' % self.name


class Email(db.Model):
    value = db.Column(db.String(120), primary_key=True)

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '<Email %r>' % self.value


class EmailMailingList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(120), db.ForeignKey('email.value'))
    email = db.relationship('Email')
    mailing_list_id = db.Column(db.Integer, db.ForeignKey('mailing_list.id'))
    mailing_list = db.relationship('MailingList')

    def __init__(self, email, mailing_list):
        self.email = email
        self.email_id = email.value
        self.mailing_list = mailing_list
        self.mailing_list_id = mailing_list.id

    def __repr__(self):
        return '<Email %r to MailingList %r>' % (self.email_id, self.mailing_list_id)
