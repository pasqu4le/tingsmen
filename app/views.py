from app import app, security
import utils
from flask import g, render_template, abort, redirect, url_for, request, get_template_attribute
from flask_security import current_user
from flask_admin.contrib import sqla
from database import *
import forms
from sqlalchemy.sql import func
from wtforms import TextAreaField


# ---------------------------------------------- ROUTING FUNCTIONS
@app.route('/', methods=('GET', 'POST'))
def home():
    # not allowed user handling:
    if not current_user.is_authenticated:
        options = {
            'title': 'Welcome',
            'pages': Page.query.all(),
            'current_user': current_user,
        }
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
        'pages': Page.query.all(),
        'current_user': current_user,
        'posts': posts,
        'some_topics': Topic.query[:10],
        'topics_all': Topic.query.all(),
        'more_topics_number': Topic.query.count(),
        'submit_post_form': forms.PostForm(),
        'form_init_js': form_init_js
    }
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
        'current_user': current_user,
        'current_page': current_page,
        'pages': Page.query.all()
    }
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
        'pages': Page.query.all(),
        'current_user': current_user,
        'current_topic': current_topic,
        'posts': posts,
        'some_topics': Topic.query[:10],
        'topics_all': Topic.query.all(),
        'more_topics_number': Topic.query.count(),
        'submit_post_form': forms.PostForm(),
        'form_init_js': form_init_js
    }
    return render_template("topic.html", **options)


@app.route('/topics/')
def topics():
    topic_list = Topic.query.all()
    options = {
        'title': 'Topics',
        'pages': Page.query.all(),
        'topic_list': topic_list,
        'current_user': current_user,
    }
    return render_template("topics.html", **options)


@app.route('/user/<username>/')
def user(username):
    return redirect("/user/" + username + "/post/")


@app.route('/settings/', methods=('GET', 'POST'))
def settings():
    if not current_user.is_authenticated:
        return redirect('/')
    form = forms.SettingsForm()
    messages = []
    if form.validate_on_submit():
        if form.username.data:
            current_user.username = form.username.data
            messages.append('You username was correctly changed')
        messages.append('Settings saved!')
        db.session.add(current_user)
        db.session.commit()
    options = {
        'title': 'settings',
        'pages': Page.query.all(),
        'current_user': current_user,
        'settings_form': form,
        'messages': messages
    }
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
        'pages': Page.query.all(),
        'current_user': current_user,
        'user': main_user,
        'posts': posts,
        'posts_group': group,
        'current_page': subpage,
        'user_pages': ['post', 'upvotes', 'downvotes'],
        'topics_all': Topic.query.all(),
        'submit_post_form': forms.PostForm(),
        'form_init_js': form_init_js
    }
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
        'pages': Page.query.all(),
        'current_user': current_user,
        'main_post': main_post,
        'old_parent': old_parent,
        'children': main_post.get_children(),
        'some_topics': Topic.query[:10],
        'topics_all': Topic.query.all(),
        'more_topics_number': Topic.query.count(),
        'submit_post_form': forms.PostForm(),
        'form_init_js': form_init_js
    }
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
        'pages': Page.query.all(),
        'current_user': current_user,
        'proposal': proposal,
        'statuses': ['all', 'open', 'pending'],
        'posts': Post.get_more(group='topic', name=proposal.topic.name),
        'topics_all': Topic.query.all(),
        'submit_post_form': forms.PostForm(),
        'form_init_js': form_init_js
    }
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
        'pages': Page.query.all(),
        'current_user': current_user,
        'statuses': ['all', 'open', 'pending'],
        'current_status': status,
        'proposals': proposals,
        'description': description
    }
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
        'pages': Page.query.all(),
        'current_user': current_user,
        'law': law,
        'posts': Post.get_more(group='topic', name=law.topic.name),
        'topics_all': Topic.query.all(),
        'submit_post_form': forms.PostForm(),
        'statuses': LawStatus.query.all(),
        'form_init_js': form_init_js
    }
    return render_template("law.html", **options)


@app.route('/laws/group/<group_name>/', methods=('GET', 'POST'))
def law_group(group_name):
    return redirect("/laws/group/" + group_name + "/approved/")


@app.route('/laws/group/<group_name>/<status_name>/', methods=('GET', 'POST'))
def law_group_status(group_name, status_name):
    # ajax request handling
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('load_more_laws', load_more_laws)
        return g.sijax.process_request()
    # non-ajax handling:
    group = LawGroup.query.filter_by(name=group_name).first()
    current_status = LawStatus.query.filter_by(name=status_name).first()
    if not (group and current_status):
        abort(404)
    options = {
        'title': ' '.join([group_name, 'laws -', status_name]),
        'pages': Page.query.all(),
        'current_user': current_user,
        'group': group,
        'laws': Law.get_more(group_name=group_name, status_name=status_name),
        'current_status': current_status,
        'statuses': LawStatus.query.all()
    }
    return render_template("law_group.html", **options)


@app.route('/laws/')
def all_laws():
    return redirect("/laws/status/approved/")


@app.route('/laws/status/<status_name>/', methods=('GET', 'POST'))
def law_status(status_name):
    # ajax request handling
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('load_more_laws', load_more_laws)
        return g.sijax.process_request()
    # non-ajax handling:
    current_status = LawStatus.query.filter_by(name=status_name).first()
    if not current_status:
        abort(404)
    options = {
        'title': ' '.join([status_name, 'laws']),
        'pages': Page.query.all(),
        'current_user': current_user,
        'current_status': current_status,
        'laws': Law.get_more(status_name=status_name),
        'statuses': LawStatus.query.all()
    }
    return render_template("law_status.html", **options)


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
        proposal = Proposal(description=form.description.data, poster=current_user, poster_id=current_user.id,
                            date=func.now())
        db.session.add(proposal)
        db.session.flush()
        proposal.set_vote_day()
        prop_tpc = Topic.query.filter_by(name="proposal." + str(proposal.id)).first()
        if not prop_tpc:
            prop_tpc = Topic(name="proposal." + str(proposal.id))
            db.session.add(prop_tpc)
        proposal.topic = prop_tpc
        proposal.topic_id = prop_tpc.id
        for content, groups in [(e.data['content'], e.data['groups']) for e in form.new_laws.entries]:
            if content:
                law = Law(content=content, date=func.now())
                db.session.add(law)
                db.session.flush()
                law_tpc = Topic.query.filter_by(name="law." + str(law.id)).first()
                if not law_tpc:
                    law_tpc = Topic(name="law." + str(law.id))
                    db.session.add(law_tpc)
                law.topic = law_tpc
                law.topic_id = law_tpc.id
                for group_name in groups:
                    if group_name != 'Base':
                        group = LawGroup.query.filter_by(name=group_name).first()
                        if group:
                            # group must exist before
                            law.group.append(group)
                proposed = LawStatus.query.filter_by(name='proposed').first()
                if proposed:
                    law.status.append(proposed)
                db.session.add(law)
                proposal.add_laws.append(law)
        for law_id in [e.data for e in form.remove_laws.entries]:
            if law_id:
                law = Law.query.filter_by(id=law_id).first()
                if law:
                    proposal.remove_laws.append(law)
        db.session.add(proposal)
        db.session.commit()
        return redirect("/proposal/" + str(proposal.id))
    return new_proposal(form)


def new_proposal(form):
    options = {
        'title': 'propose',
        'pages': Page.query.all(),
        'current_user': current_user,
        'proposal_form': form
    }
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
        'pages': Page.query.all(),
        'message': 'The page you are looking for cannot be found',
        'current_user': current_user
    }
    return render_template("error.html", **options)


@app.errorhandler(403)
def permission_denied(error):
    options = {
        'code': 403,
        'pages': Page.query.all(),
        'message': 'Access forbidden',
        'current_user': current_user
    }
    return render_template("error.html", **options)


# ---------------------------------------------- SIJAX FUNCTIONS
def vote_post(obj_response, post_id, up):
    post = Post.query.filter_by(id=post_id).first()
    if post and current_user.is_authenticated:
        if up:
            if current_user in post.upvotes:
                post.upvotes.remove(current_user)
            else:
                if current_user in post.downvotes:
                    post.downvotes.remove(current_user)
                post.upvotes.append(current_user)
        else:
            if current_user in post.downvotes:
                post.downvotes.remove(current_user)
            else:
                if current_user in post.upvotes:
                    post.upvotes.remove(current_user)
                post.downvotes.append(current_user)
        db.session.commit()
        obj_response.html('#post_vote_' + post_id, str(post.points()))
        obj_response.attr('#post_vote_' + post_id, 'class', post.current_vote_style(current_user))


def vote_proposal(obj_response, proposal_id, up):
    proposal = Proposal.query.filter_by(id=proposal_id).first()
    if proposal and current_user.is_authenticated and proposal.is_open:
        if up:
            if current_user in proposal.upvotes:
                proposal.upvotes.remove(current_user)
            else:
                if current_user in proposal.downvotes:
                    proposal.downvotes.remove(current_user)
                proposal.upvotes.append(current_user)
        else:
            if current_user in proposal.downvotes:
                proposal.downvotes.remove(current_user)
            else:
                if current_user in proposal.upvotes:
                    proposal.upvotes.remove(current_user)
                proposal.downvotes.append(current_user)
        db.session.commit()
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
        post = Post(content=form.content.data, poster=current_user, poster_id=current_user.id, date=func.now())
        if form.parent_id.data:
            post.parent_id = int(form.parent_id.data)
        for tn in form.topics.data.split():
            topic_name = utils.get_topic_name(tn)
            if topic_name:
                tpc = Topic.query.filter_by(name=topic_name).first()
                if not tpc:
                    tpc = Topic(name=topic_name, description='')
                    db.session.add(tpc)
                post.topics.append(tpc)
        db.session.add(post)
        db.session.commit()
        # update the new post and it's parent edit_date (recursively)
        post.update_edit_date()
        db.session.commit()
        if form.parent_id.data:
            par_id = form.parent_id.data
            render_comment = get_template_attribute('macros.html', 'render_comment')
            obj_response.html_prepend(''.join(['#post-', par_id, '-comments']),
                                      render_comment(post, current_user).unescape())
            # update parent comments counter
            obj_response.script(''.join(['$("#load_comment_button_', par_id, '").children(".badge").html(',
                                         str(Post.query.filter_by(parent_id=par_id).count()), ')']))
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
        # deactivate the button to avoid multiple spawning
        obj_response.script('$("#load_comment_button_' + str(post_id) + '").attr("onclick", "")')


def load_more_laws(obj_response, group_name, status_name, older_than):
    laws = Law.get_more(group_name=group_name, status_name=status_name, older_than=older_than)
    render_law = get_template_attribute('macros.html', 'render_law')
    more_laws_panel = get_template_attribute('macros.html', 'more_laws_panel')
    if laws:
        for law in laws:
            obj_response.html_append('#laws-container', render_law(law, current_user, actions_footer=True).unescape())
        obj_response.html('#load_more_container', more_laws_panel(group_name, status_name, laws[-1].date).unescape())
        # refresh and re-enable waypoint to achieve continuous loading
        obj_response.script('Waypoint.refreshAll()')
        obj_response.script('Waypoint.enableAll()')
    else:
        obj_response.html('#load_more_container', more_laws_panel(group_name, status_name, None).unescape())


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
