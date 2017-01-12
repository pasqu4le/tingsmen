import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore
from flask_admin import Admin
from flask_migrate import Migrate
from flask_gravatar import Gravatar
from flask_misaka import Misaka
import flask_sijax

app = Flask(__name__)
# set configuration keys and take them from environment variables
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SIJAX_STATIC_PATH'] = 'app/static/js/sijax/'
app.config['SIJAX_JSON_URI'] = 'app/static/js/sijax/json2.js'
app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = ('username', 'email')
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
app.config['SECURITY_PASSWORD_SALT'] = os.environ['SECRET_SALT']
# use misaka for markdown
Misaka(app)
# use sijax for ajax requests
flask_sijax.Sijax(app)
# Gravatar setup
gravatar = Gravatar(app, size=150, rating='x', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)
# SQLAlchemy and migration setup
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# imported after app and db creation because of dependencies
from app import database, forms

# Security setup
user_datastore = SQLAlchemyUserDatastore(db, database.User, database.Role)
security = Security(app, user_datastore, login_form=forms.CustomLoginForm)

# imported after app, db and user_datastore creation because of dependencies
from app import views

# Admin setup
admin = Admin(app, name='tingmen', template_mode='bootstrap3')
admin.add_view(views.ModelView(database.User, db.session))
admin.add_view(views.ModelView(database.Role, db.session))
admin.add_view(views.ModelView(database.MailingList, db.session))
admin.add_view(views.ModelView(database.Post, db.session))
admin.add_view(views.ModelView(database.Topic, db.session))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
