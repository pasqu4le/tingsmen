import os
import utils
from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore
from flask_admin import Admin
from flask_migrate import Migrate
from flask_gravatar import Gravatar
from flask_misaka import Misaka
from misaka import HTML_SKIP_HTML
from flask_mail import Mail
from flask_compress import Compress
from flask_sijax import Sijax

app = Flask(__name__)
# set configuration keys and take them from environment variables
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SIJAX_STATIC_PATH'] = 'app/static/js/sijax/'
app.config['SIJAX_JSON_URI'] = 'app/static/js/sijax/json2.js'
app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = ('username', 'email')
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
app.config['SECURITY_PASSWORD_SALT'] = os.environ['SECRET_SALT']
app.config['SECURITY_CONFIRMABLE'] = True
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_CHANGEABLE'] = True
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'tingsmen@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = True

# Mail creation
mail = Mail(app)
# use misaka for markdown
Misaka(app, renderer=utils.CustomMisakaRenderer(flags=HTML_SKIP_HTML), autolink=True, underline=True, smartypants=True,
       strikethrough=True)
# use sijax for ajax requests
Sijax(app)
# Gravatar setup
gravatar = Gravatar(app, size=150, rating='x', default='retro', force_default=False, force_lower=False, use_ssl=False,
                    base_url=None)
# SQLAlchemy and migration setup
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# imported after app and db creation because of dependencies
from app import database, forms

# Security setup
user_datastore = SQLAlchemyUserDatastore(db, database.User, database.Role)
sec_options = {
    'login_form': forms.CustomLoginForm,
    'confirm_register_form': forms.CustomRegisterForm,
    'forgot_password_form': forms.CustomForgotPasswordForm,
    'send_confirmation_form': forms.CustomSendConfirmationForm
}
security = Security(app, user_datastore, **sec_options)

# imported after app, db and user_datastore creation because of dependencies
from app import views

# Admin setup
admin = Admin(app, name='Tingsmen', template_mode='bootstrap3')
admin.add_view(views.AdminModelView(database.Globals, db.session))
admin.add_view(views.AdminModelView(database.Page, db.session))
admin.add_view(views.AdminModelView(database.MailingList, db.session))
admin.add_view(views.AdminModelView(database.User, db.session))
admin.add_view(views.AdminModelView(database.Role, db.session))
admin.add_view(views.AdminModelView(database.Notification, db.session))
admin.add_view(views.AdminModelView(database.Post, db.session))
admin.add_view(views.AdminModelView(database.Topic, db.session))
admin.add_view(views.AdminModelView(database.Proposal, db.session))
admin.add_view(views.AdminModelView(database.Law, db.session))
admin.add_view(views.AdminModelView(database.LawStatus, db.session))
admin.add_view(views.AdminModelView(database.LawGroup, db.session))

# use compress to gzip compression
Compress(app)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
