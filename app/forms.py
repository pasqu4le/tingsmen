import flask_security
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email


class EmailForm(FlaskForm):
    email = StringField('email', validators=[DataRequired(), Email()], render_kw={'placeholder': 'Email address', 'class': 'form-control'})


class CustomLoginForm(flask_security.forms.LoginForm):
    email = StringField('email', validators=[DataRequired(), Email()], render_kw={'placeholder': 'Username or Email Address', 'class': 'form-control'})
    password = PasswordField('password', validators=[DataRequired()], render_kw={'placeholder': 'Password', 'class': 'form-control'})
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login', render_kw={'placeholder': 'Login', 'class': 'btn btn-lg btn-primary btn-block'})
