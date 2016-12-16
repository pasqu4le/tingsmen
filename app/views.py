from app import app, db
from flask import render_template, abort
import database
import forms


@app.route('/')
def home():
    return render_template("index.html", title="Welcome")


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
        lnk = database.EmailMailingList.query.filter_by(mailing_list_id=ml.id, email_id=em.value).all()
        if lnk:
            errors.append("This email is already registered to this mailing list")
        else:
            lnk = database.EmailMailingList(em, ml)
            db.session.add(lnk)
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
            bridge = database.EmailMailingList.query.filter_by(email_id=em.value, mailing_list_id=ml.id).first()
            if not bridge:
                errors.append("This email is already not subscribed to this mailing list")
            else:
                db.session.delete(bridge)
                db.session.commit()
                db.session.flush()
                return render_template(template, title=title, name=mailing_list)
    errors.extend([v for value in form.errors.values() for v in value])
    return render_template(template, title=title, form=form, name=mailing_list, errors=errors)
