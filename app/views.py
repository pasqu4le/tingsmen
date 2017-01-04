from app import app, db
from flask import g, render_template, abort, redirect, url_for, request, get_template_attribute
from flask_security import current_user
from flask_admin.contrib import sqla
from flask_misaka import markdown
import database
import forms
from sqlalchemy.sql import func


# ---------------------------------------------- ROUTING FUNCTIONS
@app.route('/', methods=('GET', 'POST'))
def home():
    # not allowed user handling:
    if not current_user.is_authenticated:
        return render_template("index.html", title="Welcome")
    # ajax request handling
    form_init_js = g.sijax.register_upload_callback('post_form', submit_post)
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('vote_post', vote_post)
        return g.sijax.process_request()
    # non-ajax handling:
    options = {
        'title': 'Home',
        'current_user': current_user,
        'posts': database.Post.query.all(),
        'topics': database.Topic.query.all(),
        'submit_post_form': forms.PostForm(next_url=request.url),
        'form_init_js': form_init_js
    }
    return render_template("home.html", **options)


@app.route('/topic/<topic_name>/', methods=('GET', 'POST'))
def topic(topic_name):
    # not allowed user handling:
    if not current_user.is_authenticated:
        return redirect("/")
    # ajax request handling
    form_init_js = g.sijax.register_upload_callback('post_form', submit_post)
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('vote_post', vote_post)
        return g.sijax.process_request()
    # non-ajax handling:
    main_topic = database.Topic.query.filter_by(name=topic_name).first()
    options = {
        'title': '#' + main_topic.name,
        'current_user': current_user,
        'main_topic': main_topic,
        'posts': main_topic.posts,
        'topics': database.Topic.query.all(),
        'submit_post_form': forms.PostForm(next_url=request.url),
        'form_init_js': form_init_js
    }
    return render_template("topic.html", **options)


@app.route('/user/<username>/')
def user(username):
    return redirect("/user/" + username + "/post/")


@app.route('/user/<username>/<subpage>/', methods=('GET', 'POST'))
def user_page(username, subpage):
    # not allowed user handling:
    if not current_user.is_authenticated:
        return redirect("/")
    # ajax request handling
    form_init_js = g.sijax.register_upload_callback('post_form', submit_post)
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('vote_post', vote_post)
        return g.sijax.process_request()
    # non-ajax handling:
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
        'form_init_js': form_init_js
    }
    return render_template("user.html", **options)


@app.route('/post/<post_id>/', methods=('GET', 'POST'))
def post(post_id):
    # not allowed user handling:
    if not current_user.is_authenticated:
        return redirect("/")
    # ajax request handling
    form_init_js = g.sijax.register_upload_callback('post_form', submit_post)
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('vote_post', vote_post)
        return g.sijax.process_request()
    # non-ajax handling:
    main_post = database.Post.query.filter_by(id=post_id).first()
    options = {
        'title': 'Post',
        'current_user': current_user,
        'main_post': main_post,
        'children': get_children(main_post),
        'topics': database.Topic.query.all(),
        'submit_post_form': forms.PostForm(next_url=request.url),
        'form_init_js': form_init_js
    }
    return render_template("post.html", **options)


def get_children(parent_post, d=0):
    # utility function to get a post children tree
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
    return render_template('subscribe.html', title='Subscribe', name=mailing_list)


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


# ---------------------------------------------- SIJAX FUNCTIONS
def vote_post(obj_response, post_id, up):
    pst = database.Post.query.filter_by(id=post_id).first()
    if up:
        if current_user in pst.upvotes:
            pst.upvotes.remove(current_user)
        else:
            if current_user in pst.downvotes:
                pst.downvotes.remove(current_user)
            pst.upvotes.append(current_user)
    else:
        if current_user in pst.downvotes:
            pst.downvotes.remove(current_user)
        else:
            if current_user in pst.upvotes:
                pst.upvotes.remove(current_user)
            pst.downvotes.append(current_user)
    db.session.commit()
    obj_response.html('#post_vote_' + post_id, str(pst.points()))
    obj_response.attr('#post_vote_' + post_id, 'class', pst.current_vote_style(current_user))


def submit_post(obj_response, files, form_values):
    form = forms.PostForm(**form_values)
    if form.validate():
        # markdown options and content
        mark_opt = {
            'autolink': True,
            'underline': True,
            'smartypants': True,
            'strikethrough': True,
            'skip_html': True
        }
        content = markdown(form.content.data, **mark_opt)
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
        render_post = get_template_attribute('macros.html', 'render_post')
        obj_response.html_prepend('#post-container', render_post(pst, current_user).unescape())
        obj_response.script("$('#postModal').modal('hide');")
        form.reset()
    render_post_form = get_template_attribute('macros.html', 'render_post_form')
    obj_response.html('#post_form_container', render_post_form(form, current_user).unescape())
