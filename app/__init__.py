import os
import database
import forms
from flask import Flask, render_template, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# take configuration keys from environment variables:
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
# database:
db = SQLAlchemy(app.application())
db.create_all()


@app.route('/')
def home():
    return render_template("home.html", title="Welcome")


@app.route('/subscribe/<mailing_list>/', methods=('GET', 'POST'))
def subscribe(mailing_list):
    ml = database.MailingList(mailing_list)
    if not database.MailingList.query.filter_by(name='mailing_list').first():
        database.db.session.add(ml)
        return "mailinglist has been added right now"
    else:
        return "was alredy there"
    form = forms.EmailForm()
    if form.validate_on_submit():
        return render_template("subscribe.html", title="Subscribe", name=mailing_list)
    return render_template("subscribe.html", title="Subscribe", form=form, name=mailing_list)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
