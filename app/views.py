from app import app
from flask import g, render_template, abort, redirect, url_for, request, get_template_attribute
from flask_security import current_user
from flask_admin.contrib import sqla
from flask_misaka import markdown
from database import *
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
        g.sijax.register_callback('load_more_posts', load_more_posts)
        g.sijax.register_callback('vote_post', vote_post)
        return g.sijax.process_request()
    # non-ajax handling:
    posts = Post.get_more()
    options = {
        'title': 'Home',
        'current_user': current_user,
        'posts': posts,
        'topics': Topic.query.all(),
        'submit_post_form': forms.PostForm(next_url=request.url),
        'form_init_js': form_init_js
    }
    return render_template("home.html", **options)


@app.route('/topic/<topic_name>/', methods=('GET', 'POST'))
def topic(topic_name):
    # ajax request handling
    form_init_js = g.sijax.register_upload_callback('post_form', submit_post)
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('load_more_posts', load_more_posts)
        g.sijax.register_callback('vote_post', vote_post)
        return g.sijax.process_request()
    # non-ajax handling:
    main_topic = Topic.query.filter_by(name=topic_name).first()
    if not main_topic:
        abort(404)
    posts = Post.get_more(group='topic', name=topic_name)
    options = {
        'title': '#' + main_topic.name,
        'current_user': current_user,
        'main_topic': main_topic,
        'posts': posts,
        'topics': Topic.query.all(),
        'submit_post_form': forms.PostForm(next_url=request.url),
        'form_init_js': form_init_js
    }
    return render_template("topic.html", **options)


@app.route('/user/<username>/')
def user(username):
    return redirect("/user/" + username + "/post/")


@app.route('/user/<username>/<subpage>/', methods=('GET', 'POST'))
def user_page(username, subpage):
    # ajax request handling
    form_init_js = g.sijax.register_upload_callback('post_form', submit_post)
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('load_more_posts', load_more_posts)
        g.sijax.register_callback('vote_post', vote_post)
        return g.sijax.process_request()
    # non-ajax handling:
    main_user = User.query.filter_by(username=username).first()
    if not main_user:
        abort(404)
    posts = []
    group = 'user'
    if subpage == 'post':
        posts = Post.get_more(group='user', name=username)
    elif subpage == 'upvotes':
        posts = Post.get_more(group='upvotes', name=username)
        group = 'upvotes'
    elif subpage == 'downvotes':
        posts = Post.get_more(group='downvotes', name=username)
        group = 'downvotes'
    options = {
        'title': main_user.username,
        'current_user': current_user,
        'user': main_user,
        'posts': posts,
        'posts_group': group,
        'current_page': subpage,
        'user_pages': ['post', 'upvotes', 'downvotes'],
        'submit_post_form': forms.PostForm(next_url=request.url),
        'form_init_js': form_init_js
    }
    return render_template("user.html", **options)


@app.route('/post/<post_id>/', methods=('GET', 'POST'))
def post(post_id):
    # ajax request handling
    form_init_js = g.sijax.register_upload_callback('post_form', submit_post)
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('vote_post', vote_post)
        return g.sijax.process_request()
    # non-ajax handling:
    main_post = Post.query.filter_by(id=post_id).first()
    if not main_post:
        abort(404)
    # oldest parent:
    old_parent = None
    if main_post.parent:
        old_parent = main_post.parent
        while old_parent.parent:
            old_parent = old_parent.parent
    options = {
        'title': 'Post',
        'current_user': current_user,
        'main_post': main_post,
        'old_parent': old_parent,
        'children': main_post.get_children(),
        'topics': Topic.query.all(),
        'submit_post_form': forms.PostForm(next_url=request.url),
        'form_init_js': form_init_js
    }
    return render_template("post.html", **options)


@app.route('/subscribe/<mailing_list>/', methods=('GET', 'POST'))
def subscribe(mailing_list):
    ml = MailingList.query.filter_by(name=mailing_list).first()
    if not ml:
        abort(404)
    return redirect(ml.url)


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


# ---------------------------------------------- ERROR PAGES

@app.errorhandler(404)
def page_not_found(error):
    return render_template("error.html", code=404, message="The page you are looking for can't be found", current_user=current_user)


@app.errorhandler(403)
def permission_denied(error):
    return render_template("error.html", code=403, message="Access forbidden", current_user=current_user)


# ---------------------------------------------- SIJAX FUNCTIONS
def vote_post(obj_response, post_id, up):
    pst = Post.query.filter_by(id=post_id).first()
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


def load_more_posts(obj_response, group, name, older_than):
    posts = Post.get_more(group=group, name=name, older_than=older_than)
    render_post = get_template_attribute('macros.html', 'render_post')
    more_posts_panel = get_template_attribute('macros.html', 'more_posts_panel')
    if posts:
        for pst in posts:
            obj_response.html_append('#post-container', render_post(pst, current_user).unescape())
        obj_response.html('#load_more_container', more_posts_panel(group, name, posts[-1].date).unescape())
    else:
        obj_response.html('#load_more_container', more_posts_panel(group, name, None).unescape())


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
        pst = Post(content=content, poster=current_user, poster_id=current_user.id, date=func.now())
        if form.parent_id.data:
            pst.parent_id = int(form.parent_id.data)
        for tn in form.topics.data.split():
            topic_name = tn.strip('#').lower()
            tpc = Topic.query.filter_by(name=topic_name).first()
            if not tpc:
                tpc = Topic(name=topic_name, description='')
                db.session.add(tpc)
            pst.topics.append(tpc)
        db.session.add(pst)
        db.session.commit()
        render_post = get_template_attribute('macros.html', 'render_post')
        obj_response.html_prepend('#post-container', render_post(pst, current_user).unescape())
        obj_response.script("$('#postModal').modal('hide');")
        obj_response.script("$('html, body').animate({ scrollTop: $('#post-%s').position().top }, 500);" % str(pst.id))
        form.reset()
    render_post_form = get_template_attribute('macros.html', 'render_post_form')
    obj_response.html('#post_form_container', render_post_form(form, current_user).unescape())
