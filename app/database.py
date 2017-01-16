from app import db
from flask_security import UserMixin, RoleMixin


class MailingList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    url = db.Column(db.String(50), unique=True)

    def __repr__(self):
        return self.name


class Globals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(30), unique=True)
    value = db.Column(db.String(200))

    def __repr__(self):
        return self.key

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return self.name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return self.username

post_upvote = db.Table('post_upvote',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('post_id', db.Integer, db.ForeignKey('post.id')))

post_downvote = db.Table('post_downvote',
                         db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                         db.Column('post_id', db.Integer, db.ForeignKey('post.id')))

post_topic = db.Table('post_topic',
                      db.Column('topic_id', db.Integer(), db.ForeignKey('topic.id')),
                      db.Column('post_id', db.Integer, db.ForeignKey('post.id')))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1000))
    date = db.Column(db.DateTime())
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    poster = db.relationship("User", backref=db.backref('posts', lazy='dynamic'))
    parent_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    children = db.relationship("Post", backref=db.backref('parent', remote_side=[id]))
    upvotes = db.relationship('User', secondary=post_upvote, backref=db.backref('upvoted', lazy='dynamic'))
    downvotes = db.relationship('User', secondary=post_downvote, backref=db.backref('downvoted', lazy='dynamic'))
    topics = db.relationship('Topic', secondary=post_topic, backref=db.backref('posts', lazy='dynamic'))

    @staticmethod
    def get_more(num=5, group=None, name=None, older_than=None):
        query = Post.query
        if group and name:
            if group == 'user':
                query = query.filter(Post.poster.has(username=name))
            elif group == 'topic':
                query = query.filter(Post.topics.any(name=name))
            elif group == 'upvotes':
                query = query.filter(Post.upvotes.any(username=name))
            elif group == 'downvotes':
                query = query.filter(Post.downvotes.any(username=name))
        if older_than:
            query = query.filter(Post.date < older_than)
        return query.order_by(Post.date.desc())[:num]

    def get_children(self, d=0):
        # utility function to get a post children tree
        res = []
        depth = d
        if depth < 3:
            depth = d + 1
        if self.children:
            for child in self.children:
                res.append((child, depth))
                res.extend(child.get_children(d=depth))
        return res

    def current_vote_style(self, user):
        # returns the correct bootstrap class for the text displaying if and how a user voted on this post
        if user in self.upvotes:
            return 'text-success'
        if user in self.downvotes:
            return 'text-danger'
        return 'text-muted'

    def points(self):
        return len(self.upvotes) - len(self.downvotes)

    def __repr__(self):
        return "Post n." + str(self.id) + " by " + str(self.poster)


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(500))

    def __repr__(self):
        return "Topic: #" + self.name

proposal_upvote = db.Table('proposal_upvote',
                           db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                           db.Column('proposal_id', db.Integer, db.ForeignKey('proposal.id')))

proposal_downvote = db.Table('proposal_downvote',
                             db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                             db.Column('proposal_id', db.Integer, db.ForeignKey('proposal.id')))


class Proposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(2000))
    date = db.Column(db.DateTime())
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    poster = db.relationship("User", backref=db.backref('proposals', lazy='dynamic'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    topic = db.relationship("Topic")
    upvotes = db.relationship('User', secondary=proposal_upvote, backref=db.backref('upvoted_prop', lazy='dynamic'))
    downvotes = db.relationship('User', secondary=proposal_downvote, backref=db.backref('downvoted_prop', lazy='dynamic'))

    def __repr__(self):
        return "Proposal number: " + str(self.id)

law_add = db.Table('law_add',
                   db.Column('law_id', db.Integer(), db.ForeignKey('law.id')),
                   db.Column('proposal_id', db.Integer, db.ForeignKey('proposal.id')))

law_remove = db.Table('law_remove',
                      db.Column('law_id', db.Integer(), db.ForeignKey('law.id')),
                      db.Column('proposal_id', db.Integer, db.ForeignKey('proposal.id')))


class Law(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime())
    content = db.Column(db.String(1000))
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    topic = db.relationship("Topic")
    add_by = db.relationship('Proposal', secondary=law_add, backref=db.backref('add_laws', lazy='dynamic'))
    remove_by = db.relationship('Proposal', secondary=law_remove, backref=db.backref('remove_laws', lazy='dynamic'))

    @staticmethod
    def get_more(num=5, group_name=None, status_name=None, older_than=None):
        query = Law.query
        if status_name:
            query = query.filter(Law.status.any(name=status_name))
        if group_name:
            query = query.filter(Law.group.any(name=group_name))
        if older_than:
            query = query.filter(Law.date < older_than)
        return query.order_by(Law.date.desc())[:num]

    def __repr__(self):
        return "Law number: " + str(self.id)

law_law_status = db.Table('law_law_status',
                          db.Column('law_id', db.Integer(), db.ForeignKey('law.id')),
                          db.Column('law_status_id', db.Integer, db.ForeignKey('law_status.id')))


class LawStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    description = db.Column(db.String(200))
    laws = db.relationship('Law', secondary=law_law_status, backref=db.backref('status', lazy='dynamic'))

    def __repr__(self):
        return "Law status: " + self.name

law_law_group = db.Table('law_law_group',
                         db.Column('law_id', db.Integer(), db.ForeignKey('law.id')),
                         db.Column('law_group_id', db.Integer, db.ForeignKey('law_group.id')))


class LawGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    description = db.Column(db.String(200))
    laws = db.relationship('Law', secondary=law_law_group, backref=db.backref('group', lazy='dynamic'))

    def __repr__(self):
        return "Law group: " + self.name
