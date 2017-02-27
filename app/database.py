from app import db
from datetime import timedelta, date
from flask_security import UserMixin, RoleMixin
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property


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


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    title = db.Column(db.String(50))
    content = db.Column(db.String(1000))

    def __repr__(self):
        return self.name


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

    def change_settings(self, username=None):
        if username:
            self.username = username
            db.session.add(self)
            db.session.commit()

    def __repr__(self):
        return self.username


notification_author = db.Table('notification_author',
                               db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                               db.Column('notification_id', db.Integer, db.ForeignKey('notification.id')))


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship("User")
    source_id = db.Column(db.String(10))
    source_type = db.Column(db.String(20))
    source_action = db.Column(db.String(20))
    link = db.Column(db.String(30))
    date = db.Column(db.DateTime())
    seen = db.Column(db.Boolean())
    authors = db.relationship('User', secondary=notification_author)

    def __repr__(self):
        return str(self.id)

post_upvote = db.Table('post_upvote',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('post_id', db.Integer, db.ForeignKey('post.id')))

post_downvote = db.Table('post_downvote',
                         db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                         db.Column('post_id', db.Integer, db.ForeignKey('post.id')))

post_topic = db.Table('post_topic',
                      db.Column('topic_id', db.Integer(), db.ForeignKey('topic.id')),
                      db.Column('post_id', db.Integer, db.ForeignKey('post.id')))

post_subscription = db.Table('post_subscription',
                             db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                             db.Column('post_id', db.Integer, db.ForeignKey('post.id')))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1000))
    date = db.Column(db.DateTime())
    last_edit_date = db.Column(db.DateTime())
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    poster = db.relationship("User", backref=db.backref('posts', lazy='dynamic'))
    parent_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    children = db.relationship("Post", backref=db.backref('parent', remote_side=[id]))
    upvotes = db.relationship('User', secondary=post_upvote, backref=db.backref('upvoted', lazy='dynamic'))
    downvotes = db.relationship('User', secondary=post_downvote, backref=db.backref('downvoted', lazy='dynamic'))
    topics = db.relationship('Topic', secondary=post_topic, backref=db.backref('posts', lazy='dynamic'))
    subscribed = db.relationship('User', secondary=post_subscription, backref=db.backref('subscribed_posts',
                                                                                         lazy='dynamic'))

    # static method to get a list of following posts (by date) in a 'group'
    @staticmethod
    def get_more(num=5, group=None, name=None, older_than=None):
        # start filtering by parent-only
        query = Post.query.filter(Post.parent_id.is_(None))
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
            query = query.filter(Post.last_edit_date < older_than)
        return query.order_by(Post.last_edit_date.desc())[:num]

    @staticmethod
    def submit(content, poster, parent_id, topic_names):
        post = Post(content=content, poster=poster, poster_id=poster.id, date=func.now())
        if parent_id:
            post.parent_id = parent_id
        # set topics
        for topic_name in topic_names:
            if topic_name:
                tpc = Topic.retrieve(topic_name)
                post.topics.append(tpc)
        db.session.add(post)
        # update the new post and it's parent edit_date (recursively)
        post.update_edit_date()
        db.session.commit()
        return post

    def vote(self, user, up):
        if up:
            if user in self.upvotes:
                self.upvotes.remove(user)
            else:
                if user in self.downvotes:
                    self.downvotes.remove(user)
                self.upvotes.append(user)
        else:
            if user in self.downvotes:
                self.downvotes.remove(user)
            else:
                if user in self.upvotes:
                    self.upvotes.remove(user)
                self.downvotes.append(user)
        db.session.commit()

    def update_edit_date(self, new_date=None):
        if not new_date:
            new_date = self.date
        self.last_edit_date = new_date
        if self.parent:
            self.parent.update_edit_date(new_date)

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

    @staticmethod
    def sane_name(name):
        topic_name = []
        after_hyphens = False
        for l in name:
            if l.isalnum():
                topic_name.append(l)
                after_hyphens = False
            elif l == '-' and not after_hyphens:
                topic_name.append(l)
                after_hyphens = True
        return ''.join(topic_name).strip('-').lower()

    @staticmethod
    def retrieve(name):
        # sanitize the name
        name = Topic.sane_name(name)
        # make if does not exists and return:
        topic = Topic.query.filter_by(name=name).first()
        if not topic:
            topic = Topic(name=name)
            db.session.add(topic)
            db.session.commit()
        return topic

    def __repr__(self):
        return "Topic: #" + self.name

proposal_upvote = db.Table('proposal_upvote',
                           db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                           db.Column('proposal_id', db.Integer, db.ForeignKey('proposal.id')))

proposal_downvote = db.Table('proposal_downvote',
                             db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                             db.Column('proposal_id', db.Integer, db.ForeignKey('proposal.id')))

proposal_subscription = db.Table('proposal_subscription',
                                 db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                                 db.Column('proposal_id', db.Integer, db.ForeignKey('proposal.id')))


class Proposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(2000))
    date = db.Column(db.DateTime())
    vote_day = db.Column(db.Date())
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    poster = db.relationship("User", backref=db.backref('proposals', lazy='dynamic'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    topic = db.relationship("Topic")
    upvotes = db.relationship('User', secondary=proposal_upvote, backref=db.backref('upvoted_prop', lazy='dynamic'))
    downvotes = db.relationship('User', secondary=proposal_downvote, backref=db.backref('downvoted_prop',
                                                                                        lazy='dynamic'))
    subscribed = db.relationship('User', secondary=proposal_subscription, backref=db.backref('subscribed_prop',
                                                                                             lazy='dynamic'))

    def set_vote_day(self):
        self.vote_day = self.date.date() + timedelta(days=7-self.date.weekday())

    @staticmethod
    def submit(description, poster, new_laws, remove_laws):
        proposal = Proposal(description=description, poster=poster, poster_id=poster.id, date=func.now())
        db.session.add(proposal)
        db.session.flush()
        # set vote day
        proposal.set_vote_day()
        # set topic
        tpc = Topic.retrieve("proposal-" + str(proposal.id))
        proposal.topic = tpc
        proposal.topic_id = tpc.id
        # status for the newly added laws
        proposed = LawStatus.query.filter_by(name='proposed').first()
        # create and link new laws
        for content, groups in new_laws:
            if content:
                law = Law(content=content, date=func.now())
                db.session.add(law)
                db.session.flush()
                # set topic
                tpc = Topic.retrieve("law-" + str(law.id))
                law.topic = tpc
                law.topic_id = tpc.id
                # set groups
                for group_name in groups:
                    # new laws cannot be in the Base group
                    if group_name != 'Base':
                        group = LawGroup.query.filter_by(name=group_name).first()
                        if group:
                            # group must already exist
                            law.group.append(group)
                # set the law status as proposed
                law.status.append(proposed)
                # insert the law in the proposal
                proposal.add_laws.append(law)
        # create and link laws to remove
        for law_id in remove_laws:
            if law_id:
                law = Law.query.filter_by(id=law_id).first()
                if law:
                    proposal.remove_laws.append(law)
        # commit everything and return
        db.session.commit()
        return proposal

    @hybrid_property
    def is_open(self):
        return date.today() == self.vote_day

    @hybrid_property
    def is_pending(self):
        return date.today() < self.vote_day

    @staticmethod
    def get_more(num=5, open=False, pending=False, older_than=None):
        query = Proposal.query
        if open:
            query = query.filter_by(is_open=True)
        if pending:
            query = query.filter_by(is_pending=True)
        if older_than:
            query = query.filter(Proposal.date < older_than)
        return query.order_by(Proposal.date.desc())[:num]

    def vote(self, user, up):
        if self.is_open:
            if up:
                if user in self.upvotes:
                    self.upvotes.remove(user)
                else:
                    if user in self.downvotes:
                        self.downvotes.remove(user)
                    self.upvotes.append(user)
            else:
                if user in self.downvotes:
                    self.downvotes.remove(user)
                else:
                    if user in self.upvotes:
                        self.upvotes.remove(user)
                    self.downvotes.append(user)
            db.session.commit()

    def approved(self):
        return self.points() > 0

    def rejected(self):
        return self.points() < 0

    def confirmed(self):
        if self.approved():
            proposed = LawStatus.query.filter_by(name='proposed').first()
            approved = LawStatus.query.filter_by(name='approved').first()
            removed = LawStatus.query.filter_by(name='removed').first()
            # check that all statuses do exist
            if proposed and approved and removed:
                for law in self.add_laws:
                    if proposed in law.status or approved not in law.status:
                        return False
                for law in self.remove_laws:
                    if removed not in law.status:
                        return False
                return True
        elif self.rejected():
            proposed = LawStatus.query.filter_by(name='proposed').first()
            rejected = LawStatus.query.filter_by(name='rejected').first()
            # check that all statuses do exist
            if proposed and rejected:
                for law in self.add_laws:
                    if proposed in law.status or rejected not in law.status:
                        return False
                return True
        # if anything went wrong or the proposal is open:
        return False

    def confirm(self):
        # method to set all laws statuses in this proposal correctly
        if self.approved():
            proposed = LawStatus.query.filter_by(name='proposed').first()
            approved = LawStatus.query.filter_by(name='approved').first()
            removed = LawStatus.query.filter_by(name='removed').first()
            # check that all statuses do exist
            if proposed and approved and removed:
                for law in self.add_laws:
                    if proposed in law.status:
                        law.status.remove(proposed)
                    if approved not in law.status:
                        law.status.append(approved)
                for law in self.remove_laws:
                    law.status = [removed]
        elif self.rejected():
            proposed = LawStatus.query.filter_by(name='proposed').first()
            rejected = LawStatus.query.filter_by(name='rejected').first()
            # check that all statuses do exist
            if proposed and rejected:
                for law in self.add_laws:
                    if proposed in law.status:
                        law.status.remove(proposed)
                    if rejected not in law.status:
                        law.status.append(rejected)
        # commit the changes at the end
        db.session.commit()

    def points(self):
        return len(self.upvotes) - len(self.downvotes)

    def current_vote_style(self, user):
        # returns the correct bootstrap class for the text displaying if and how a user voted on this proposal
        if user in self.upvotes:
            return 'text-success'
        if user in self.downvotes:
            return 'text-danger'
        return 'text-muted'

    def __repr__(self):
        return "Proposal number: " + str(self.id)

law_add = db.Table('law_add',
                   db.Column('law_id', db.Integer(), db.ForeignKey('law.id')),
                   db.Column('proposal_id', db.Integer, db.ForeignKey('proposal.id')))

law_remove = db.Table('law_remove',
                      db.Column('law_id', db.Integer(), db.ForeignKey('law.id')),
                      db.Column('proposal_id', db.Integer, db.ForeignKey('proposal.id')))

law_subscription = db.Table('law_subscription',
                            db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                            db.Column('law_id', db.Integer, db.ForeignKey('law.id')))


class Law(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime())
    content = db.Column(db.String(1000))
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    topic = db.relationship("Topic")
    add_by = db.relationship('Proposal', secondary=law_add, backref=db.backref('add_laws', lazy='dynamic'))
    remove_by = db.relationship('Proposal', secondary=law_remove, backref=db.backref('remove_laws', lazy='dynamic'))
    subscribed = db.relationship('User', secondary=law_subscription, backref=db.backref('subscribed_laws',
                                                                                        lazy='dynamic'))

    @staticmethod
    def get_more(num=5, group_name=None, status_name=None, order='id', last=None):
        query = Law.query
        if status_name:
            query = query.filter(Law.status.any(name=status_name))
        if group_name:
            query = query.filter(Law.group.any(name=group_name))
        if order == 'id':
            if last:
                query = query.filter(Law.id > int(last))
            query = query.order_by(Law.id)
        elif order == 'date':
            if last:
                query = query.filter(Law.date < last)
            query = query.order_by(Law.date.desc())
        return query[:num]

    def __repr__(self):
        return "Law number: " + str(self.id)

law_law_status = db.Table('law_law_status',
                          db.Column('law_id', db.Integer(), db.ForeignKey('law.id')),
                          db.Column('law_status_id', db.Integer, db.ForeignKey('law_status.id')))


class LawStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(200))
    laws = db.relationship('Law', secondary=law_law_status, backref=db.backref('status', lazy='dynamic'))

    def __repr__(self):
        return "Law status: " + self.name

law_law_group = db.Table('law_law_group',
                         db.Column('law_id', db.Integer(), db.ForeignKey('law.id')),
                         db.Column('law_group_id', db.Integer, db.ForeignKey('law_group.id')))


class LawGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(200))
    laws = db.relationship('Law', secondary=law_law_group, backref=db.backref('group', lazy='dynamic'))

    def __repr__(self):
        return "Law group: " + self.name
