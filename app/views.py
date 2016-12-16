from app import app, db, user_datastore
from flask import render_template, abort
from flask_security import current_user
import database
import forms


# configure initial value of the database
@app.before_first_request
def before():
    db.create_all()
    if not database.MailingList.query.filter_by(name='news').first():
        ml = database.MailingList('news')
        db.session.add(ml)
        db.session.commit()
    if not database.User.query.filter_by(username='matt').first():
        user_datastore.create_user(username='matt', email='matt@nobien.net', password='password')
        db.session.commit()


# ROUTING
@app.route('/')
def home():
    return render_template("index.html", title="Welcome")


@app.route('/example/')
def example():
    if current_user.is_authenticated:
        return "you are welcome"
    else:
        return "this is not your place"


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
            em = database.Email(mail)
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
