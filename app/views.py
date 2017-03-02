from app import app, security
from flask import g, render_template, abort, redirect, url_for, request, get_template_attribute
from flask_security import current_user
from flask_admin.contrib import sqla
from database import *
import forms
from wtforms import TextAreaField


def base_options():
    # a function for the options required by every page
    return {
        'pages': Page.query.all(),
        'current_user': current_user
    }


# ---------------------------------------------- ROUTING FUNCTIONS
@app.route('/', methods=('GET', 'POST'))
def home():
    # not authenticated user handling:
    if not current_user.is_authenticated:
        options = {
            'title': 'Welcome',
        }
        options.update(base_options())
        return render_template("index.html", **options)
    # ajax request handling
    form_init_js = g.sijax.register_upload_callback('post_form', submit_post)
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('load_more_posts', load_more_posts)
        g.sijax.register_callback('load_comments', load_comments)
        g.sijax.register_callback('vote_post', vote_post)
        return g.sijax.process_request()
    # non-ajax handling:
    posts = Post.get_more()
    options = {
        'title': 'Home',
        'posts': posts,
        'some_topics': Topic.query[:10],
        'topics_all': Topic.query.all(),
        'more_topics_number': Topic.query.count(),
        'submit_post_form': forms.PostForm(),
        'form_init_js': form_init_js
    }
    options.update(base_options())
    return render_template("home.html", **options)


@app.route('/cookies/')
def cookie_policy():
    return render_template("cookies.html", title='Cookie policy')


@app.route('/page/<page_name>/')
def view_page(page_name):
    # non-ajax handling:
    current_page = Page.query.filter_by(name=page_name).first()
    if not current_page:
        abort(404)
    options = {
        'title': current_page.name,
        'current_page': current_page
    }
    options.update(base_options())
    return render_template("page.html", **options)


@app.route('/topic/<topic_name>/', methods=('GET', 'POST'))
def topic(topic_name):
    # ajax request handling
    form_init_js = g.sijax.register_upload_callback('post_form', submit_post)
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('load_more_posts', load_more_posts)
        g.sijax.register_callback('load_comments', load_comments)
        g.sijax.register_callback('vote_post', vote_post)
        return g.sijax.process_request()
    # non-ajax handling:
    current_topic = Topic.query.filter_by(name=topic_name).first()
    if not current_topic:
        abort(404)
    posts = Post.get_more(group='topic', name=topic_name)
    options = {
        'title': '#' + current_topic.name,
        'current_topic': current_topic,
        'posts': posts,
        'some_topics': Topic.query[:10],
        'topics_all': Topic.query.all(),
        'more_topics_number': Topic.query.count(),
        'submit_post_form': forms.PostForm(),
        'form_init_js': form_init_js
    }
    options.update(base_options())
    return render_template("topic.html", **options)


@app.route('/topics/')
def topics():
    topic_list = Topic.query.all()
    options = {
        'title': 'Topics',
        'topic_list': topic_list
    }
    options.update(base_options())
    return render_template("topics.html", **options)


@app.route('/notifications/')
def notifications():
    if current_user.is_authenticated:
        notifs = current_user.get_notifications()
        options = {
            'title': 'Topics',
            'notifs': notifs
        }
        options.update(base_options())
        return render_template("notifications.html", **options)
    return redirect('/')


@app.route('/notification/<notif_id>/')
def open_notification(notif_id):
    if current_user.is_authenticated:
        notif = Notification.query.filter_by(id=notif_id).first()
        # check if the notification exists and is for current_user
        if notif and notif.user == current_user:
            if not notif.seen:
                notif.seen = True
                db.session.commit()
            return redirect(notif.link)
    return redirect('/')


@app.route('/user/<username>/')
def view_user(username):
    return redirect("/user/" + username + "/post/")


@app.route('/settings/', methods=('GET', 'POST'))
def settings():
    if not current_user.is_authenticated:
        return redirect('/')
    form = forms.SettingsForm()
    messages = []
    if form.validate_on_submit():
        if form.username.data:
            current_user.change_settings(username=form.username.data)
            messages.append('You username was correctly changed')
        messages.append('Settings saved!')
    options = {
        'title': 'settings',
        'settings_form': form,
        'messages': messages
    }
    options.update(base_options())
    return render_template("settings.html", **options)


@app.route('/user/<username>/<subpage>/', methods=('GET', 'POST'))
def user_page(username, subpage):
    # ajax request handling
    form_init_js = g.sijax.register_upload_callback('post_form', submit_post)
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('load_more_posts', load_more_posts)
        g.sijax.register_callback('load_comments', load_comments)
        g.sijax.register_callback('vote_post', vote_post)
        return g.sijax.process_request()
    # non-ajax handling:
    user = User.query.filter_by(username=username).first()
    if not user:
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
        'title': user.username,
        'user': user,
        'posts': posts,
        'posts_group': group,
        'current_page': subpage,
        'user_pages': ['post', 'upvotes', 'downvotes'],
        'topics_all': Topic.query.all(),
        'submit_post_form': forms.PostForm(),
        'form_init_js': form_init_js
    }
    options.update(base_options())
    return render_template("user.html", **options)


@app.route('/post/<post_id>/', methods=('GET', 'POST'))
def view_post(post_id):
    # ajax request handling
    form_init_js = g.sijax.register_upload_callback('post_form', submit_post)
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('load_comments', load_comments)
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
        'main_post': main_post,
        'old_parent': old_parent,
        'children': main_post.get_children(),
        'some_topics': Topic.query[:10],
        'topics_all': Topic.query.all(),
        'more_topics_number': Topic.query.count(),
        'submit_post_form': forms.PostForm(),
        'form_init_js': form_init_js
    }
    options.update(base_options())
    return render_template("post.html", **options)


@app.route('/proposal/<proposal_id>/', methods=('GET', 'POST'))
def view_proposal(proposal_id):
    # ajax request handling
    form_init_js = g.sijax.register_upload_callback('post_form', submit_post)
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('load_more_posts', load_more_posts)
        g.sijax.register_callback('load_comments', load_comments)
        g.sijax.register_callback('vote_post', vote_post)
        g.sijax.register_callback('vote_proposal', vote_proposal)
        g.sijax.register_callback('confirm_proposal', confirm_proposal)
        return g.sijax.process_request()
    # non-ajax handling:
    proposal = Proposal.query.filter_by(id=proposal_id).first()
    if not proposal:
        abort(404)
    options = {
        'title': 'Proposal',
        'proposal': proposal,
        'statuses': ['all', 'open', 'pending'],
        'posts': Post.get_more(group='topic', name=proposal.topic.name),
        'topics_all': Topic.query.all(),
        'submit_post_form': forms.PostForm(),
        'form_init_js': form_init_js
    }
    options.update(base_options())
    return render_template("proposal.html", **options)


@app.route('/proposals/')
def view_proposals():
    # show open proposals if there is at least one
    if Proposal.query.filter_by(is_open=True).count():
        return redirect("/proposals/open/")
    return redirect("/proposals/pending/")


@app.route('/proposals/<status>/', methods=('GET', 'POST'))
def proposal_status(status):
    # ajax request handling
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('vote_proposal', vote_proposal)
        g.sijax.register_callback('confirm_proposal', confirm_proposal)
        g.sijax.register_callback('load_more_proposals', load_more_proposals)
        return g.sijax.process_request()
    # non-ajax handling:
    proposals = []
    description = None
    if status == 'open':
        proposals = Proposal.get_more(open=True)
        description = 'can be voted today'
    if status == 'pending':
        proposals = Proposal.get_more(pending=True)
        description = 'waiting for their vote day'
    elif status == 'all':
        proposals = Proposal.get_more()
    options = {
        'title': ' '.join([status, 'proposals']),
        'statuses': ['all', 'open', 'pending'],
        'current_status': status,
        'proposals': proposals,
        'description': description
    }
    options.update(base_options())
    return render_template("proposals.html", **options)


@app.route('/law/<law_id>/', methods=('GET', 'POST'))
def view_law(law_id):
    # ajax request handling
    form_init_js = g.sijax.register_upload_callback('post_form', submit_post)
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('load_more_posts', load_more_posts)
        g.sijax.register_callback('load_comments', load_comments)
        g.sijax.register_callback('vote_post', vote_post)
        return g.sijax.process_request()
    # non-ajax handling:
    law = Law.query.filter_by(id=law_id).first()
    if not law:
        abort(404)
    options = {
        'title': 'Law',
        'law': law,
        'posts': Post.get_more(group='topic', name=law.topic.name),
        'topics_all': Topic.query.all(),
        'submit_post_form': forms.PostForm(),
        'statuses': LawStatus.query.all(),
        'form_init_js': form_init_js
    }
    options.update(base_options())
    return render_template("law.html", **options)


@app.route('/laws/')
def all_laws():
    return redirect("/laws/all/active/id/")


@app.route('/laws/<group_name>/<status_name>/<order>/', methods=('GET', 'POST'))
def view_laws(group_name, status_name, order):
    # ajax request handling
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('load_more_laws', load_more_laws)
        return g.sijax.process_request()
    # non-ajax handling:
    current_group = LawGroup.query.filter_by(name=group_name).first()
    current_status = LawStatus.query.filter_by(name=status_name).first()
    if not (current_status and (current_group or group_name == 'all')):
        abort(404)
    if group_name == 'all':
        laws = Law.get_more(status_name=status_name, order=order)
    else:
        laws = Law.get_more(group_name=group_name, status_name=status_name, order=order)
    options = {
        'title': ' '.join([group_name, 'laws', '-', status_name]),
        'laws': laws,
        'groups': LawGroup.query.all(),
        'current_group': current_group,
        'statuses': LawStatus.query.all(),
        'current_status': current_status,
        'orders': ['id', 'date'],
        'order': order
    }
    options.update(base_options())
    return render_template("laws.html", **options)


@app.route('/new-proposal/remove/<law_id>/')
def new_proposal_remove(law_id):
    form = forms.ProposalForm()
    form.remove_laws.pop_entry()
    form.remove_laws.append_entry(law_id)
    return new_proposal(form)


@app.route('/new-proposal/change/<proposal_id>/')
def new_proposal_change(proposal_id):
    form = forms.ProposalForm()
    proposal = Proposal.query.filter_by(id=proposal_id).first()
    if proposal:
        form.description.data = proposal.description
        if proposal.add_laws.count():
            form.new_laws.pop_entry()
            for law in proposal.add_laws:
                form.new_laws.append_entry({'content': law.content, 'groups': [gr.name for gr in law.group]})
        if proposal.remove_laws.count():
            form.remove_laws.pop_entry()
            for law in proposal.remove_laws:
                form.remove_laws.append_entry(law.id)
    return new_proposal(form)


@app.route('/new-proposal/', methods=('GET', 'POST'))
def submit_proposal():
    form = forms.ProposalForm()
    if current_user.is_authenticated and form.validate_on_submit():
        proposal = Proposal.submit(form.description.data, current_user,
                                   [(e.data['content'], e.data['groups']) for e in form.new_laws.entries],
                                   [e.data for e in form.remove_laws.entries])
        return redirect("/proposal/" + str(proposal.id))
    return new_proposal(form)


def new_proposal(form):
    options = {
        'title': 'propose',
        'proposal_form': form
    }
    options.update(base_options())
    return render_template("new_proposal.html", **options)


@app.route('/subscribe/<mailing_list>/', methods=('GET', 'POST'))
def subscribe(mailing_list):
    ml = MailingList.query.filter_by(name=mailing_list).first()
    if not ml:
        abort(404)
    return redirect(ml.url)


# Custom admin model view class
class AdminModelView(sqla.ModelView):
    form_overrides = {
        'description': TextAreaField,
        'content': TextAreaField,
    }

    def is_accessible(self):
        if current_user.is_active and current_user.is_authenticated and current_user.has_role('admin'):
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


# ---------------------------------------------- SECURITY CONTEXT PROCESSORS

@security.register_context_processor
def security_register_processor():
    limit = int(Globals.query.filter_by(key='user_limit').first().value)
    available = False
    if limit == 0 or User.query.count() < limit:
        available = True
    return {'register_available': available}


# ---------------------------------------------- ERROR PAGES

@app.errorhandler(404)
def page_not_found(error):
    options = {
        'code': 404,
        'message': 'The page you are looking for cannot be found'
    }
    options.update(base_options())
    return render_template("error.html", **options)


@app.errorhandler(403)
def permission_denied(error):
    options = {
        'code': 403,
        'message': 'Access forbidden'
    }
    options.update(base_options())
    return render_template("error.html", **options)


# ---------------------------------------------- SIJAX FUNCTIONS
def vote_post(obj_response, post_id, up):
    post = Post.query.filter_by(id=post_id).first()
    if post and current_user.is_authenticated:
        post.vote(current_user, up)
        obj_response.html('#post_vote_' + post_id, str(post.points()))
        obj_response.attr('#post_vote_' + post_id, 'class', post.current_vote_style(current_user))


def vote_proposal(obj_response, proposal_id, up):
    proposal = Proposal.query.filter_by(id=proposal_id).first()
    if proposal and current_user.is_authenticated:
        proposal.vote(current_user, up)
        obj_response.html('#proposal_vote_' + proposal_id, str(proposal.points()))
        obj_response.attr('#proposal_vote_' + proposal_id, 'class', proposal.current_vote_style(current_user))


def confirm_proposal(obj_response, proposal_id):
    proposal = Proposal.query.filter_by(id=proposal_id).first()
    if proposal and current_user.has_role('admin'):
        proposal.confirm()
        obj_response.alert('proposal confirmed')
    else:
        obj_response.alert('proposal not confirmed')


def load_more_posts(obj_response, group, name, older_than):
    posts = Post.get_more(group=group, name=name, older_than=older_than)
    render_post = get_template_attribute('macros.html', 'render_post')
    more_posts_panel = get_template_attribute('macros.html', 'more_posts_panel')
    if posts:
        for post in posts:
            obj_response.html_append('#post-container', render_post(post, current_user).unescape())
        obj_response.html('#load_more_container', more_posts_panel(group, name, posts[-1].date).unescape())
        # refresh and re-enable waypoint to achieve continuous loading
        obj_response.script('Waypoint.refreshAll()')
        obj_response.script('Waypoint.enableAll()')
    else:
        obj_response.html('#load_more_container', more_posts_panel(group, name, None).unescape())


def submit_post(obj_response, files, form_values):
    form = forms.PostForm(**form_values)
    if form.validate():
        parent_id = None
        if form.parent_id.data:
            parent_id = form.parent_id.data
            post = Post.submit(form.content.data, current_user, int(parent_id), form.topics.data.split())
        else:
            post = Post.submit(form.content.data, current_user, None, form.topics.data.split())

        if parent_id:
            render_comment = get_template_attribute('macros.html', 'render_comment')
            obj_response.html_prepend(''.join(['#post-', parent_id, '-comments']),
                                      render_comment(post, current_user).unescape())
            # update parent comments counter
            obj_response.script(''.join(['$("#load_comment_button_', parent_id, '").children(".badge").html(',
                                         str(Post.query.filter_by(parent_id=parent_id).count()), ')']))
        else:
            render_post = get_template_attribute('macros.html', 'render_post')
            obj_response.html_prepend('#post-container', render_post(post, current_user).unescape())
        obj_response.script("$('#collapsable_post_form').collapse('hide');")
        form.reset()
    render_post_form = get_template_attribute('macros.html', 'render_post_form')
    obj_response.html('#collapsable_post_form', render_post_form(form, current_user).unescape())
    # register again the sijax upload plugin
    obj_response.script('sjxUpload.registerForm({"callback": "post_form_upload", "formId": "post_form"});')


def load_comments(obj_response, post_id, depth):
    comments = Post.query.filter_by(parent_id=post_id).order_by(Post.date)
    if comments:
        render_comment = get_template_attribute('macros.html', 'render_comment')
        # clear the comments displayed (to avoid double loading of inserted comments)
        obj_response.html(''.join(['#post-', str(post_id), '-comments']), '')
        for comment in comments:
            obj_response.html_append(''.join(['#post-', str(post_id), '-comments']),
                                     render_comment(comment, current_user, depth).unescape())
        # change the button to hide the comments if pressed again
        obj_response.script(''.join(['$("#load_comment_button_', str(post_id), '").attr("onclick", "hide_comments(',
                                     str(post_id), ',', str(depth), ')")']))


def load_more_laws(obj_response, group_name, status_name, order, last):
    laws = Law.get_more(group_name=group_name, status_name=status_name, order=order, last=last)
    render_law = get_template_attribute('macros.html', 'render_law')
    more_laws_panel = get_template_attribute('macros.html', 'more_laws_panel')
    if laws:
        for law in laws:
            obj_response.html_append('#laws-container', render_law(law, current_user, actions_footer=True).unescape())
        if order == 'id':
            panel = more_laws_panel(group_name, status_name, order, laws[-1].id).unescape()
        elif order == 'date':
            panel = more_laws_panel(group_name, status_name, order, laws[-1].date).unescape()
        obj_response.html('#load_more_container', panel)
        # refresh masonry to load the new laws correctly
        obj_response.script('$(".masonry-grid").masonry( "reloadItems" )')
        obj_response.script('$(".masonry-grid").masonry()')
        # refresh and re-enable waypoint to achieve continuous loading
        obj_response.script('Waypoint.refreshAll()')
        obj_response.script('Waypoint.enableAll()')
    else:
        obj_response.html('#load_more_container', more_laws_panel().unescape())


def load_more_proposals(obj_response, open, pending, older_than):
    proposals = Proposal.get_more(open=open, pending=pending, older_than=older_than)
    render_proposal = get_template_attribute('macros.html', 'render_proposal')
    more_proposals_panel = get_template_attribute('macros.html', 'more_proposals_panel')
    if proposals:
        for proposal in proposals:
            obj_response.html_append('#proposals-container', render_proposal(proposal, current_user).unescape())
        obj_response.html('#load_more_container',
                          more_proposals_panel(proposals[-1].date, open=open, pending=pending).unescape())
        # refresh and re-enable waypoint to achieve continuous loading
        obj_response.script('Waypoint.refreshAll()')
        obj_response.script('Waypoint.enableAll()')
    else:
        obj_response.html('#load_more_container', more_proposals_panel(None).unescape())
