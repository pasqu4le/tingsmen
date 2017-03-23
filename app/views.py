from app import app, security
from flask import g, render_template, abort, redirect, url_for, request, get_template_attribute, flash, jsonify
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
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        g.sijax.register_callback('toggle_subscription', toggle_subscription)
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


@app.route('/cookies/', methods=('GET', 'POST'))
def cookie_policy():
    # ajax request handling
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('update_notifications', update_notifications)
        return g.sijax.process_request()
    # non-ajax handling:
    return render_template("cookies.html", title='Cookie policy')


@app.route('/page/<page_name>/', methods=('GET', 'POST'))
def view_page(page_name):
    # ajax request handling
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('update_notifications', update_notifications)
        return g.sijax.process_request()
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
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        g.sijax.register_callback('toggle_subscription', toggle_subscription)
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


@app.route('/topics/', methods=('GET', 'POST'))
def topics():
    # ajax request handling
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        return g.sijax.process_request()
    # non-ajax handling:
    topic_list = Topic.query.all()
    options = {
        'title': 'Topics',
        'topic_list': topic_list
    }
    options.update(base_options())
    return render_template("topics.html", **options)


@app.route('/notifications/', methods=('GET', 'POST'))
def notifications():
    if current_user.is_authenticated:
        # ajax request handling
        if g.sijax.is_sijax_request:
            g.sijax.register_callback('load_more_notifications', load_more_notifications)
            g.sijax.register_callback('update_notifications', update_notifications)
            g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
            return g.sijax.process_request()
        # non-ajax handling:
        notifs = Notification.get_more(current_user, num=30)
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
    # ajax request handling
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        return g.sijax.process_request()
    # non-ajax handling:
    form = forms.SettingsForm()
    messages = []
    if form.validate_on_submit():
        if form.delete.data:
            if form.del_confirm.data:
                if form.del_posts.data:
                    User.wipe(current_user, True)
                else:
                    User.wipe(current_user, False)
                flash('Your user has been successfully deleted, farewell!')
                return redirect('/')
            else:
                form.del_confirm.errors.append('You need to check this if you want to delete yourself')
        elif form.username.data:
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


@app.route('/delete/post/<post_id>/', methods=('GET', 'POST'))
def delete_post(post_id):
    if current_user.is_authenticated:
        # ajax request handling
        if g.sijax.is_sijax_request:
            g.sijax.register_callback('update_notifications', update_notifications)
            g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
            return g.sijax.process_request()
        # non-ajax handling:
        post = Post.query.filter_by(id=post_id).first()
        if post and post.poster == current_user:
            post.wipe()
        else:
            flash('You cannot delete a post that does not exists or is not yours')
        return redirect(post.link_to())
    return redirect('/')


@app.route('/edit/post/<post_id>/', methods=('GET', 'POST'))
def edit_post(post_id):
    if current_user.is_authenticated:
        # ajax request handling
        if g.sijax.is_sijax_request:
            g.sijax.register_callback('update_notifications', update_notifications)
            g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
            return g.sijax.process_request()
        # non-ajax handling:
        options = {
            'title': 'Edit post',
            'form_type': 'post'
        }
        form = forms.PostForm()
        post = Post.query.filter_by(id=post_id).first()
        if not post:
            options['message'] = 'You are trying to edit a post that does not exists'
        elif post.poster != current_user:
            options['message'] = 'You are trying to modify a post that is not yours'
        elif form.validate_on_submit():
            post.edit(form.content.data)
            options['message'] = 'Your post has been successfully modified'
        else:
            form.content.data = post.content
            options['form'] = form
        options.update(base_options())
        return render_template("edit.html", **options)
    return redirect('/')


@app.route('/edit/proposal/<proposal_id>/', methods=('GET', 'POST'))
def edit_proposal(proposal_id):
    if current_user.is_authenticated:
        # ajax request handling
        if g.sijax.is_sijax_request:
            g.sijax.register_callback('update_notifications', update_notifications)
            g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
            return g.sijax.process_request()
        # non-ajax handling:
        options = {
            'title': 'Edit proposal',
            'form_type': 'proposal'
        }
        form = forms.ProposalForm()
        proposal = Proposal.query.filter_by(id=proposal_id).first()
        if not proposal:
            options['message'] = 'You are trying to edit a proposal that does not exists'
        elif proposal.poster != current_user:
            options['message'] = 'You are trying to modify a proposal that is not yours'
        elif not proposal.is_pending:
            options['message'] = "You can modify a proposal only before it's vote day"
        elif form.validate_on_submit():
            proposal.edit(form.description.data, [(e.data['content'], e.data['groups']) for e in form.new_laws.entries],
                          [e.data for e in form.remove_laws.entries])
            options['message'] = 'Your proposal has been successfully modified'
        else:
            form.description.data = proposal.description
            if proposal.add_laws.count():
                form.new_laws.pop_entry()
                for law in proposal.add_laws:
                    form.new_laws.append_entry({'content': law.content, 'groups': [gr.name for gr in law.group]})
            if proposal.remove_laws.count():
                form.remove_laws.pop_entry()
                for law in proposal.remove_laws:
                    form.remove_laws.append_entry(law.id)
            options['form'] = form
        options.update(base_options())
        return render_template("edit.html", **options)
    return redirect('/')


@app.route('/edit/law/<law_id>/', methods=('GET', 'POST'))
def edit_law(law_id):
    if current_user.is_authenticated:
        # ajax request handling
        if g.sijax.is_sijax_request:
            g.sijax.register_callback('update_notifications', update_notifications)
            g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
            return g.sijax.process_request()
        # non-ajax handling:
        options = {
            'title': 'Edit law',
            'form_type': 'law'
        }
        form = forms.LawForm()
        law = Law.query.filter_by(id=law_id).first()
        if not law:
            options['message'] = 'You are trying to edit a law that does not exists'
        elif law.add_by[-1].poster != current_user:
            options['message'] = 'You are trying to modify a law that is not yours'
        elif not law.add_by[-1].is_pending:
            options['message'] = "You can modify a law only before it's vote day"
        elif form.validate_on_submit():
            law.edit(form.content.data, form.groups.data)
            options['message'] = 'Your law has been successfully modified'
        else:
            form.content.data = law.content
            form.groups.data = [gr.name for gr in law.group]
            options['form'] = form
        options.update(base_options())
        return render_template("edit.html", **options)
    return redirect('/')


@app.route('/user/<username>/<subpage>/', methods=('GET', 'POST'))
def user_page(username, subpage):
    # ajax request handling
    form_init_js = g.sijax.register_upload_callback('post_form', submit_post)
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('load_more_posts', load_more_posts)
        g.sijax.register_callback('load_comments', load_comments)
        g.sijax.register_callback('vote_post', vote_post)
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        g.sijax.register_callback('toggle_subscription', toggle_subscription)
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
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        g.sijax.register_callback('toggle_subscription', toggle_subscription)
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
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        g.sijax.register_callback('toggle_subscription', toggle_subscription)
        g.sijax.register_callback('set_law_active', set_law_active)
        g.sijax.register_callback('set_law_premature', set_law_premature)
        g.sijax.register_callback('set_law_impossible', set_law_impossible)
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
    if Proposal.query.filter_by(is_pending=True).count():
        return redirect("/proposals/pending/")
    return redirect("/proposals/all/")


@app.route('/proposals/<status>/', methods=('GET', 'POST'))
def proposal_status(status):
    # ajax request handling
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('vote_proposal', vote_proposal)
        g.sijax.register_callback('confirm_proposal', confirm_proposal)
        g.sijax.register_callback('load_more_proposals', load_more_proposals)
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        g.sijax.register_callback('toggle_subscription', toggle_subscription)
        g.sijax.register_callback('set_law_active', set_law_active)
        g.sijax.register_callback('set_law_premature', set_law_premature)
        g.sijax.register_callback('set_law_impossible', set_law_impossible)
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
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        g.sijax.register_callback('toggle_subscription', toggle_subscription)
        g.sijax.register_callback('set_law_active', set_law_active)
        g.sijax.register_callback('set_law_premature', set_law_premature)
        g.sijax.register_callback('set_law_impossible', set_law_impossible)
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
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        g.sijax.register_callback('toggle_subscription', toggle_subscription)
        g.sijax.register_callback('set_law_active', set_law_active)
        g.sijax.register_callback('set_law_premature', set_law_premature)
        g.sijax.register_callback('set_law_impossible', set_law_impossible)
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


@app.route('/new-proposal/remove/<law_id>/', methods=('GET', 'POST'))
def new_proposal_remove(law_id):
    # ajax request handling
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        return g.sijax.process_request()
    # non-ajax handling:
    form = forms.ProposalForm()
    form.remove_laws.pop_entry()
    form.remove_laws.append_entry(law_id)
    return new_proposal(form)


@app.route('/new-proposal/change/<proposal_id>/', methods=('GET', 'POST'))
def new_proposal_change(proposal_id):
    # ajax request handling
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        return g.sijax.process_request()
    # non-ajax handling:
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
    # ajax request handling
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        return g.sijax.process_request()
    # non-ajax handling:
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
    # ajax request handling
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        return g.sijax.process_request()
    # non-ajax handling:
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
def not_found(error):
    return redirect('/404/')


@app.errorhandler(403)
def permission_denied(error):
    return redirect('/403/')


@app.route('/404/', methods=('GET', 'POST'))
def page_not_found():
    # ajax request handling
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        return g.sijax.process_request()
    # non-ajax handling:
    options = {
        'code': 404,
        'message': 'The page you are looking for cannot be found'
    }
    options.update(base_options())
    return render_template("error.html", **options)


@app.route('/403/', methods=('GET', 'POST'))
def page_permission_denied(error):
    # ajax request handling
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('update_notifications', update_notifications)
        g.sijax.register_callback('set_all_notifications_seen', set_all_notifications_seen)
        return g.sijax.process_request()
    # non-ajax handling:
    options = {
        'code': 403,
        'message': 'Access forbidden'
    }
    options.update(base_options())
    return render_template("error.html", **options)


# ---------------------------------------------- APIs

@app.route('/api/topics/search/<value>/')
def api_search_topics(value):
    return jsonify({'topics': [t.to_dict() for t in Topic.query.filter(Topic.name.ilike("%" + value + "%")).all()]})


@app.route('/api/users/search/<value>/')
def api_search_users(value):
    return jsonify({'users': [u.to_dict() for u in User.query.filter(User.username.ilike("%" + value + "%")).all()]})


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
        obj_response.alert('Error: something occurred')


def set_law_active(obj_response, law_id):
    law = Law.query.filter_by(id=law_id).first()
    if law and current_user.has_role('admin'):
        law.set_active()
        obj_response.alert('law is active')
    else:
        obj_response.alert('Error: something occurred')


def set_law_premature(obj_response, law_id):
    law = Law.query.filter_by(id=law_id).first()
    if law and current_user.has_role('admin'):
        law.set_premature()
        obj_response.alert('law is premature')
    else:
        obj_response.alert('Error: something occurred')


def set_law_impossible(obj_response, law_id):
    law = Law.query.filter_by(id=law_id).first()
    if law and current_user.has_role('admin'):
        law.set_impossible()
        obj_response.alert('law is impossible')
    else:
        obj_response.alert('Error: something occurred')


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
        post = Post.submit(form.content.data, current_user, parent_id)

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


def load_more_notifications(obj_response, older_than):
    notifs = Notification.get_more(current_user, older_than=older_than)
    render_notification = get_template_attribute('macros.html', 'render_notification')
    more_notifications_panel = get_template_attribute('macros.html', 'more_notifications_panel')
    if notifs:
        for notif in notifs:
            obj_response.html_append('#notifications-container', render_notification(notif).unescape())
        obj_response.html('#load_more_container',
                          more_notifications_panel(notifs[-1].date).unescape())
        # refresh and re-enable waypoint to achieve continuous loading
        obj_response.script('Waypoint.refreshAll()')
        obj_response.script('Waypoint.enableAll()')
    else:
        obj_response.html('#load_more_container', more_notifications_panel(None).unescape())


def update_notifications(obj_response, newer_than):
    if current_user.is_authenticated and current_user.has_new_notifications(newer_than):
        # make the notifications bell green
        obj_response.script('$("#notifications_bell").attr("class", "glyphicon glyphicon-bell notif-unseen")')
        # play an unpleasant sound
        obj_response.script('document.getElementById("bleep_sound").play()')
        # update the notifications dropdown
        render_dropdown = get_template_attribute('macros.html', 'render_notifications_dropdown')
        obj_response.html('#notifications_dropdown', render_dropdown(current_user).unescape())


def set_all_notifications_seen(obj_response):
    if current_user.is_authenticated:
        # set all as seen in the database:
        current_user.set_all_notifications_seen()
        # make the notifications bell white
        obj_response.script('$("#notifications_bell").attr("class", "glyphicon glyphicon-bell")')
        # update the notifications dropdown
        render_dropdown = get_template_attribute('macros.html', 'render_notifications_dropdown')
        obj_response.html('#notifications_dropdown', render_dropdown(current_user).unescape())


def toggle_subscription(obj_response, item_type, item_id):
    render_subscription = get_template_attribute('macros.html', 'render_subscription')
    if item_type == 'proposal':
        query = Proposal.query
    elif item_type == 'law':
        query = Law.query
    elif item_type == 'post':
        query = Post.query
    else:
        return
    item = query.filter_by(id=item_id).first()
    if item:
        item.toggle_subscription(current_user)
        obj_response.html('#' + item_type + '-' + str(item_id) + '-subscription',
                          render_subscription(current_user, item, item_type).unescape())
