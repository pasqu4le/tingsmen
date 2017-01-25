from app import app, security
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
        'topics': Topic.query[:10],
        'more_topics_number': Topic.query.count(),
        'submit_post_form': forms.PostForm(),
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
    current_topic = Topic.query.filter_by(name=topic_name).first()
    if not current_topic:
        abort(404)
    posts = Post.get_more(group='topic', name=topic_name)
    options = {
        'title': '#' + current_topic.name,
        'current_user': current_user,
        'current_topic': current_topic,
        'posts': posts,
        'topics': Topic.query[:10],
        'more_topics_number': Topic.query.count(),
        'submit_post_form': forms.PostForm(),
        'form_init_js': form_init_js
    }
    return render_template("topic.html", **options)


@app.route('/topics/')
def topics():
    topic_list =  Topic.query.all()
    options = {
        'title': 'Topics',
        'topic_list': topic_list,
        'current_user': current_user,
    }
    return render_template("topics.html", **options)


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
        'submit_post_form': forms.PostForm(),
        'form_init_js': form_init_js
    }
    return render_template("user.html", **options)


@app.route('/post/<post_id>/', methods=('GET', 'POST'))
def view_post(post_id):
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
        'topics': Topic.query[:10],
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
        'current_user': current_user,
        'proposal': proposal,
        'statuses': ['all', 'open'],
        'posts': Post.get_more(group='topic', name=proposal.topic.name),
        'submit_post_form': forms.PostForm(),
        'form_init_js': form_init_js
    }
    return render_template("proposal.html", **options)


@app.route('/proposals/')
def view_proposals():
    return redirect("/proposals/open/")


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
    description = 'here is one'
    if status == 'open':
        proposals = Proposal.get_more(open=True)
    elif status == 'all':
        proposals = Proposal.get_more()
    options = {
        'title': ' '.join([status, 'proposals']),
        'current_user': current_user,
        'statuses': ['all', 'open'],
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
        g.sijax.register_callback('vote_post', vote_post)
        return g.sijax.process_request()
    # non-ajax handling:
    law = Law.query.filter_by(id=law_id).first()
    if not law:
        abort(404)
    options = {
        'title': 'Law',
        'current_user': current_user,
        'law': law,
        'posts': Post.get_more(group='topic', name=law.topic.name),
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
        'current_user': current_user,
        'current_status': current_status,
        'laws': Law.get_more(status_name=status_name),
        'statuses': LawStatus.query.all()
    }
    return render_template("law_status.html", **options)


@app.route('/new-proposal/', methods=('GET', 'POST'))
def new_empty_proposal():
    if request.method == 'POST':
        return submit_proposal()
    return new_proposal()


@app.route('/new-proposal/remove/<law_id>/', methods=('GET', 'POST'))
def new_proposal_remove(law_id):
    if request.method == 'POST':
        return submit_proposal()
    form = forms.ProposalForm()
    form.remove_laws.pop_entry()
    form.remove_laws.append_entry(law_id)
    return new_proposal(form)


@app.route('/new-proposal/change/<proposal_id>/', methods=('GET', 'POST'))
def new_proposal_change(proposal_id):
    if request.method == 'POST':
        return submit_proposal()
    proposal = Proposal.query.filter_by(id=proposal_id).first()
    if not proposal:
        return new_proposal()
    form = forms.ProposalForm()
    form.description.data = proposal.description
    if proposal.add_laws:
        form.new_laws.pop_entry()
        for law in proposal.add_laws:
            form.new_laws.append_entry({'content': law.content, 'groups': " ".join([g.name for g in law.group])})
    if proposal.remove_laws:
        form.remove_laws.pop_entry()
        for law in proposal.remove_laws:
            form.remove_laws.append_entry(law.id)
    return new_proposal(form)


def submit_proposal():
    form = forms.ProposalForm()
    if current_user.is_authenticated and form.validate_on_submit():
        proposal = Proposal(description=form.description.data, poster=current_user, poster_id=current_user.id, date=func.now())
        db.session.add(proposal)
        db.session.flush()
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
                for group_name in groups.split():
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


def new_proposal(form=None):
    if not form:
        form = forms.ProposalForm()
    options = {
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


# ---------------------------------------------- SECURITY CONTECT PROCESSORS

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
    return render_template("error.html", code=404, message="The page you are looking for can't be found", current_user=current_user)


@app.errorhandler(403)
def permission_denied(error):
    return render_template("error.html", code=403, message="Access forbidden", current_user=current_user)


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
        post = Post(content=content, poster=current_user, poster_id=current_user.id, date=func.now())
        if form.parent_id.data:
            post.parent_id = int(form.parent_id.data)
        for tn in form.topics.data.split():
            topic_name = tn.strip('#').lower()
            tpc = Topic.query.filter_by(name=topic_name).first()
            if not tpc:
                tpc = Topic(name=topic_name, description='')
                db.session.add(tpc)
            post.topics.append(tpc)
        db.session.add(post)
        db.session.commit()
        render_post = get_template_attribute('macros.html', 'render_post')
        obj_response.html_prepend('#post-container', render_post(post, current_user).unescape())
        obj_response.script("$('#postModal').modal('hide');")
        obj_response.script("$('html, body').animate({ scrollTop: $('#post-%s').position().top }, 500);" % str(post.id))
        form.reset()
    render_post_form = get_template_attribute('macros.html', 'render_post_form')
    obj_response.html('#post_form_container', render_post_form(form, current_user).unescape())


def load_more_laws(obj_response, group_name, status_name, older_than):
    laws = Law.get_more(group_name=group_name, status_name=status_name, older_than=older_than)
    render_law = get_template_attribute('macros.html', 'render_law')
    more_laws_panel = get_template_attribute('macros.html', 'more_laws_panel')
    if laws:
        for law in laws:
            obj_response.html_append('#laws-container', render_law(law, current_user).unescape())
        obj_response.html('#load_laws_container', more_laws_panel(group_name, status_name, laws[-1].date).unescape())
    else:
        obj_response.html('#load_laws_container', more_laws_panel(group_name, status_name, None).unescape())


def load_more_proposals(obj_response, open, older_than):
    proposals = Proposal.get_more(open=open, older_than=older_than)
    render_proposal = get_template_attribute('macros.html', 'render_proposal')
    more_proposals_panel = get_template_attribute('macros.html', 'more_proposals_panel')
    if proposals:
        for proposal in proposals:
            obj_response.html_append('#proposals-container', render_proposal(proposal, current_user).unescape())
        obj_response.html('#load_proposals_container', more_proposals_panel(open, proposals[-1].date).unescape())
    else:
        obj_response.html('#load_proposals_container', more_proposals_panel(open, None).unescape())
