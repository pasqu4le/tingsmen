from app import db
from flask_security import UserMixin, RoleMixin


email_mailing_list = db.Table('email_mailing_list',
                              db.Column('mailing_list_id', db.Integer(), db.ForeignKey('mailing_list.id')),
                              db.Column('email_id', db.String(120), db.ForeignKey('email.value')))


class MailingList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    emails = db.relationship('Email', secondary=email_mailing_list, backref=db.backref('mailing_lists', lazy='dynamic'))

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


roles_users = db.Table('roles_users', db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
