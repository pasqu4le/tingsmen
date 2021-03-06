from app.database import LawGroup
from flask_security.forms import email_required, email_validator, unique_user_email, valid_user_email
from flask_security.forms import LoginForm, RegisterForm, ForgotPasswordForm, SendConfirmationForm, ResetPasswordForm
from flask_wtf import FlaskForm
from flask_wtf.csrf import generate_csrf
from werkzeug.datastructures import MultiDict
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, HiddenField, FieldList, FormField,\
    SelectMultipleField, RadioField
from wtforms.validators import DataRequired, EqualTo, Email
from wtforms.widgets.core import html_params
from wtforms.widgets import HTMLString


class InlineSubmitField(BooleanField):
    class InlineButtonWidget(object):
        # Render a basic <button> field.
        input_type = 'submit'
        html_params = staticmethod(html_params)

        def __call__(self, field, **kwargs):
            kwargs.setdefault('id', field.id)
            kwargs.setdefault('type', self.input_type)
            kwargs.setdefault('value', field.id)
            return HTMLString('<button %s>%s</button>' % (self.html_params(name=field.name, **kwargs),
                                                          field.label.text))

    # Represents a <button type="submit">, allowing checking if a submit button has been pressed.
    widget = InlineButtonWidget()


class PostForm(FlaskForm):
    parent_id = HiddenField('parent_id')
    content = TextAreaField('content', validators=[DataRequired()], render_kw={'placeholder': 'Content', 'rows': '5',
                                                                               'autocomplete': 'off'})
    submit = InlineSubmitField('Post', render_kw={'class': 'btn btn-lg btn-primary btn-block'})

    def reset(self):
        # allow to reset this form fields
        blank_data = MultiDict([('csrf', generate_csrf())])
        self.process(blank_data)


class LawForm(FlaskForm):
    content = TextAreaField(render_kw={'placeholder': 'Content', 'rows': '5'})
    groups = SelectMultipleField(choices=[(g.name, g.name) for g in LawGroup.query.all() if g.name != 'Base'],
                                 render_kw={'placeholder': 'Groups', 'class': 'form-control group_form'})
    submit = InlineSubmitField('Submit', render_kw={'class': 'btn btn-lg btn-primary btn-block'})


class ProposalForm(FlaskForm):
    description = TextAreaField(validators=[DataRequired()], render_kw={'placeholder': 'Description', 'rows': '7'})
    new_laws = FieldList(FormField(LawForm), min_entries=1)
    remove_laws = FieldList(StringField(render_kw={'placeholder': 'LawNumber'}), min_entries=1)
    submit = InlineSubmitField('Submit', render_kw={'class': 'btn btn-lg btn-primary btn-block'})


class SettingsForm(FlaskForm):
    username = StringField('username', validators=[unique_user_email],
                           render_kw={'placeholder': 'Username (leave blank to avoid changes)'})
    new_password = PasswordField('new_password', render_kw={'placeholder': 'New Password (leave blank to avoid changes)'})
    new_pass_confirm = PasswordField('new_pass_confirm',
                                     validators=[EqualTo('new_password', message='Passwords do not match')],
                                     render_kw={'placeholder': 'Retype new Password'})
    current_password = PasswordField('current_password', render_kw={'placeholder': 'Your current Password'})
    delete = BooleanField('Delete my account', render_kw={'class': 'form-inline'})
    del_confirm = BooleanField('Confirm deletion', render_kw={'class': 'form-inline'})
    del_posts = BooleanField('Delete my posts as well', render_kw={'class': 'form-inline'})
    submit = InlineSubmitField('Save', render_kw={'class': 'btn btn-lg btn-primary'})


class SearchForm(FlaskForm):
    interrogation = StringField('interrogation', render_kw={'placeholder': 'Search'})
    filter = RadioField(u'Label', choices=[('all', u'All'), ('posts', u'Posts'), ('users', u'Users'), ('laws', u'Laws'),
                                           ('proposals', u'Proposals'), ('topics', u'Topics'), ('pages', u'Pages')],
                        default='all', validators=[DataRequired()], render_kw={'class': 'form-inline'})


class InviteForm(FlaskForm):
    email = StringField('email', validators=[DataRequired(), Email()], render_kw={'placeholder': 'Email'})
    sender = StringField('sender', validators=[DataRequired()], render_kw={'placeholder': 'Who are you?'})
    submit = InlineSubmitField('Send Invitation', render_kw={'class': 'btn btn-lg btn-primary'})


# ---------- custom flask-security forms


class CustomLoginForm(LoginForm):
    email = StringField('email', validators=[DataRequired()], render_kw={'placeholder': 'Username or Email Address'})
    password = PasswordField('password', validators=[DataRequired()], render_kw={'placeholder': 'Password'})
    remember = BooleanField('Remember Me', render_kw={'class': 'form-inline'})
    submit = InlineSubmitField('Login', render_kw={'class': 'btn btn-lg btn-primary btn-block'})


class CustomRegisterForm(RegisterForm):
    email = StringField('email', validators=[email_required, email_validator, unique_user_email],
                        render_kw={'placeholder': 'Email Address'})
    username = StringField('username', validators=[DataRequired(), unique_user_email],
                           render_kw={'placeholder': 'Username'})
    password = PasswordField('password', validators=[DataRequired()], render_kw={'placeholder': 'Password'})
    password_confirm = PasswordField('retype_password',
                                     validators=[EqualTo('password', message='Passwords do not match')],
                                     render_kw={'placeholder': 'Retype Password'})
    submit = InlineSubmitField('Register', render_kw={'class': 'btn btn-lg btn-primary btn-block'})


class CustomForgotPasswordForm(ForgotPasswordForm):
    email = StringField('email', validators=[email_required, email_validator, valid_user_email],
                        render_kw={'placeholder': 'Email Address'})
    submit = InlineSubmitField('Recover Password', render_kw={'class': 'btn btn-lg btn-primary btn-block'})


class CustomSendConfirmationForm(SendConfirmationForm):
    email = StringField('email', validators=[email_required, email_validator, valid_user_email],
                        render_kw={'placeholder': 'Email Address'})
    submit = InlineSubmitField('Resend Confirmation Email', render_kw={'class': 'btn btn-lg btn-primary btn-block'})


class CustomResetPasswordForm(ResetPasswordForm):
    password = PasswordField('password', validators=[DataRequired()], render_kw={'placeholder': 'Password'})
    password_confirm = PasswordField('retype_password',
                                     validators=[EqualTo('password', message='Passwords do not match')],
                                     render_kw={'placeholder': 'Retype Password'})
    submit = InlineSubmitField('Reset Password', render_kw={'class': 'btn btn-lg btn-primary btn-block'})
