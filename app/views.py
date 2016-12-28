from app import app, db
from flask import render_template, abort, redirect, url_for, request, flash
from flask_security import current_user
from flask_admin.contrib import sqla
from flask_misaka import markdown
import database
import forms
from sqlalchemy.sql import func


# ROUTING
@app.route('/')
def home():
    if current_user.is_authenticated:
        options = {
            'title': 'Home',
            'current_user': current_user,
            'posts': database.Post.query.all(),
            'topics': database.Topic.query.all(),
            'submit_post_form': forms.PostForm(next_url=request.url),
            'vote_post_form': forms.VotePostForm(next_url=request.url)
        }
        return render_template("home.html", **options)
    return render_template("index.html", title="Welcome")


@app.route('/submit/post/', methods=('GET', 'POST'))
def submit_post():
    if not current_user.is_authenticated:
        # permission denied
        abort(403)
    form = forms.PostForm()
    if form.validate_on_submit():
        content = markdown(form.content.data, autolink=True, underline=True, smartypants=True, strikethrough=True, skip_html=True)
        pst = database.Post(content=content, poster=current_user, poster_id=current_user.id, date=func.now())
        if form.parent_id.data:
            pst.parent_id = int(form.parent_id.data)
        for topic_name in form.topics.data.split():
            tpc = database.Topic.query.filter_by(name=topic_name).first()
            if not tpc:
                tpc = database.Topic(name=topic_name, description='')
                db.session.add(tpc)
            pst.topics.append(tpc)
        db.session.add(pst)
        db.session.commit()
        flash("You published your new post")
        next_url = form.next_url.data
        if not next_url:
            next_url = '/'
        return redirect(next_url)
    return render_template('submitpost.html', submit_post_form=form, current_user=current_user)


@app.route('/vote/<post_id>/', methods=('GET', 'POST'))
def vote_post(post_id):
    if not current_user.is_authenticated:
        # permission denied
        abort(403)
    form = forms.VotePostForm()
    pst = database.Post.query.filter_by(id=post_id).first()
    next_url = '/'
    if not pst:
        abort(404)
    if form.validate_on_submit():
        if form.upvote.data:
            if current_user in pst.downvotes:
                pst.downvotes.remove(current_user)
            if current_user not in pst.upvotes:
                pst.upvotes.append(current_user)
                flash("Upvoted!")
        elif form.downvote.data:
            if current_user in pst.upvotes:
                pst.upvotes.remove(current_user)
            if current_user not in pst.downvotes:
                pst.downvotes.append(current_user)
                flash("Downvoted!")
        db.session.commit()
        if form.next_url.data:
            next_url = form.next_url.data
    return redirect(next_url)


@app.route('/topic/<topic_name>/')
def topic(topic_name):
    if current_user.is_authenticated:
        main_topic = database.Topic.query.filter_by(name=topic_name).first()
        options = {
            'title': '#' + main_topic.name,
            'current_user': current_user,
            'main_topic': main_topic,
            'posts': main_topic.posts,
            'topics': database.Topic.query.all(),
            'submit_post_form': forms.PostForm(next_url=request.url),
            'vote_post_form': forms.VotePostForm(next_url=request.url)
        }
        return render_template("topic.html", **options)
    return redirect("/")


@app.route('/user/<username>/')
def user(username):
    return redirect("/user/" + username + "/post/")


@app.route('/user/<username>/<subpage>/')
def user_page(username, subpage):
    if current_user.is_authenticated:
        main_user = database.User.query.filter_by(username=username).first()
        options = {
            'title': main_user.username,
            'current_user': current_user,
            'user': main_user,
            'posts': main_user.posts,
            'upvotes': main_user.upvoted,
            'downvotes': main_user.downvoted,
            'subpage': subpage,
            'subpages': ['post', 'upvotes', 'downvotes'],
            'submit_post_form': forms.PostForm(next_url=request.url),
            'vote_post_form': forms.VotePostForm(next_url=request.url)
        }
        return render_template("user.html", **options)
    return redirect("/")


@app.route('/post/<post_id>/')
def post(post_id):
    if current_user.is_authenticated:
        main_post = database.Post.query.filter_by(id=post_id).first()
        options = {
            'title': 'Post',
            'current_user': current_user,
            'main_post': main_post,
            'children': get_children(main_post),
            'topics': database.Topic.query.all(),
            'submit_post_form': forms.PostForm(next_url=request.url),
            'vote_post_form': forms.VotePostForm(next_url=request.url)
        }
        return render_template("post.html", **options)
    return redirect("/")


def get_children(parent_post, d=0):
    res = []
    depth = d
    if depth < 3:
        depth = d+1
    if parent_post.children:
        for child in parent_post.children:
            res.append((child, depth))
            res.extend(get_children(child, d=depth))
    return res


@app.route('/subscribe/<mailing_list>/', methods=('GET', 'POST'))
def subscribe(mailing_list):
    # basics:
    title = 'Subscribe'
    template = 'subscribe.html'
    # retrieve the mailing list from the database
    ml = database.MailingList.query.filter_by(name=mailing_list).first()
    # check if mailing list exists
    if not ml:
        abort(404)
    # check if the form has been correctly filled
    form = forms.EmailForm()
    errors = []
    if form.validate_on_submit():
        # if so, add the mail to the mailing list
        mail = str(form.email.data)
        em = database.Email.query.filter_by(value=mail).first()
        # if it's not in the database add it
        if not em:
            em = database.Email(value=mail)
            db.session.add(em)
        # check if this email is already associated to this mailing list
        if em in ml.emails:
            errors.append("This email is already registered to this mailing list")
        else:
            ml.emails.append(em)
            db.session.commit()
            db.session.flush()
            return render_template(template, title=title, name=mailing_list)
    # if not, add the form errors and retry:
    errors.extend([v for value in form.errors.values() for v in value])
    return render_template(template, title=title, form=form, name=mailing_list, errors=errors)


@app.route('/unsubscribe/<mailing_list>/', methods=('GET', 'POST'))
def unsubscribe(mailing_list):
    # basics:
    title = 'Unsubscribe'
    template = 'subscribe.html'
    # retrieve the mailing list from the database
    ml = database.MailingList.query.filter_by(name=mailing_list).first()
    # check if mailing list exists
    if not ml:
        abort(404)
    form = forms.EmailForm()
    # check if the form has been correctly filled
    errors = []
    if form.validate_on_submit():
        em = database.Email.query.filter_by(value=(str(form.email.data))).first()
        if not em:
            errors.append("This email is not in the database")
        else:
            if em not in ml.emails:
                errors.append("This email is already not subscribed to this mailing list")
            else:
                ml.emails.remove(em)
                db.session.commit()
                db.session.flush()
                return render_template(template, title=title, name=mailing_list)
    errors.extend([v for value in form.errors.values() for v in value])
    return render_template(template, title=title, form=form, name=mailing_list, errors=errors)


# Custom admin model view class
class ModelView(sqla.ModelView):

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        if current_user.has_role('admin'):
            return True
        return False

    def _handle_view(self, name, **kwargs):
        # Override builtin to redirect users
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))
