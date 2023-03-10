from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User
from app.models import Style
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.widgets import  ColorInput
import re
from wtforms.validators import DataRequired, Length , Regexp
from flask_wtf.file import FileField
from flask_babel import lazy_gettext as _l

from flask import request
class AlphanumericWithDashUnderscore(object):
    """
    Validator that checks if a string contains only alphanumeric characters, hyphens, and underscores.
    """
    def __init__(self, message=None):
        if not message:
            message = 'Field must contain only alphanumeric characters, hyphens, and underscores'
        self.message = message

    def __call__(self, form, field):
        pattern = re.compile(r'^[\w-]+$')
        if not pattern.match(field.data):
            raise ValidationError(self.message)
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')

class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[
        DataRequired(), Length(min=1, max=2000)])
    img_caption = TextAreaField('Photo Caption', validators=[
        DataRequired(), Length(min=1, max=140)])
    post_img = FileField('File')
    post_vid=TextAreaField('Video Link')

    submit = SubmitField('Submit')



class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')
    profile_image = FileField('File')
    tags=TextAreaField('Tags')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')
class SubmitStyleForm(FlaskForm):
    style_nm=TextAreaField('Style Name',validators=[DataRequired(), AlphanumericWithDashUnderscore()])
    style_inspire = TextAreaField('Style Inspiration', validators=[DataRequired()])
    nm=FileField('Photo Name')
    color =  StringField('Color', widget=ColorInput())
    submit = SubmitField('Submit ')



    def __init__(self, original_style_nm, original_user_id,*args, **kwargs):
        super(SubmitStyleForm, self).__init__(*args, **kwargs)
        self.original_style_nm = original_style_nm
        self.original_user_id=original_user_id


    def validate_style_nm(self, style_nm):
        style_nm = Style.query.filter_by(style_nm=style_nm.data).first()
        if style_nm is not None:
            raise ValidationError('Please use a different style name.')
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')