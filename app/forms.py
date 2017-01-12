import flask_security
from flask_wtf import FlaskForm
from flask_wtf.csrf import generate_csrf
from werkzeug.datastructures import MultiDict
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Email
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
            return HTMLString('<button %s>%s</button>' % (self.html_params(name=field.name, **kwargs), field.label.text))

    # Represents a <button type="submit">, allowing checking if a submit button has been pressed.
    widget = InlineButtonWidget()


class PostForm(FlaskForm):
    parent_id = HiddenField('parent_id')
    content = TextAreaField('content', validators=[DataRequired()], render_kw={'rows': '8'})
    topics = StringField('topics', render_kw={'placeholder': 'Topics'})
    submit = InlineSubmitField('Post', render_kw={'placeholder': 'Post', 'class': 'btn btn-lg btn-primary btn-block'})

    def reset(self):
        # allow to reset this form fields
        blank_data = MultiDict([('csrf', generate_csrf())])
        self.process(blank_data)


class CustomLoginForm(flask_security.forms.LoginForm):
    email = StringField('email', validators=[DataRequired()], render_kw={'placeholder': 'Username or Email Address'})
    password = PasswordField('password', validators=[DataRequired()], render_kw={'placeholder': 'Password'})
    remember = BooleanField('Remember Me', render_kw={'class': 'form-inline'})
    submit = InlineSubmitField('Login', render_kw={'placeholder': 'Login', 'class': 'btn btn-lg btn-primary btn-block'})
