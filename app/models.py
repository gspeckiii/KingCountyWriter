from datetime import datetime
from app import db
from app import login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from time import time
import jwt
from app import app

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)
class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    profile_image = db.Column(db.String(20))
    tags =db.Column(db.String(4000))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    styles = db.relationship('Style', backref='stylist', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)
    def profile_img(self):
        if self.profile_image is not None:
            p_img=self.profile_image
        else:
            p_img='wizard.jpg'
        return p_img

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0
    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def followed_styles(self):
        followed = Style.query.join(
            followers, (followers.c.followed_id == Style.user_id)).filter(
            followers.c.follower_id == self.id)
        own = Style.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Style.timestamp.desc())
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(2000))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_img =db.Column(db.String(200))
    post_vid=db.Column(db.String(300))
    img_caption=db.Column(db.String(200))
    language = db.Column(db.String(5))
    def __repr__(self):
        return '<Post {}>'.format(self.body)

class Style(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp=db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    style_nm=db.Column(db.String(20), index=True, unique=True)
    style_inspire=db.Column(db.String(250))
    pan_nm = db.Column(db.String(100))
    pan_color=db.Column(db.String(10))
    ls_nm = db.Column(db.String(100))
    ls_color=db.Column(db.String(10))
    sq_nm = db.Column(db.String(100))
    sq_color=db.Column(db.String(10))
    pt_nm = db.Column(db.String(100))
    pt_color=db.Column(db.String(10))
    language = db.Column(db.String(5))
    def __repr__(self):
        return '<Style {}>'.format(self.body)






