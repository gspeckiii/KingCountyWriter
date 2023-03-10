
from flask import render_template, flash, redirect, url_for,abort
from app import app
from app.forms import LoginForm
from flask_login import current_user, login_user
from app.models import User
from flask_login import login_required
from flask import request
from werkzeug.urls import url_parse
from flask_login import logout_user
from app import db

from app.forms import RegistrationForm
from app.forms import PostForm
from app.models import Post
from app.models import Style
from datetime import datetime
from app.forms import EmptyForm
from app.forms import EditProfileForm
from app.forms import SubmitStyleForm
from app.forms import ResetPasswordRequestForm
from app.email import send_password_reset_email
from app.forms import ResetPasswordForm
from werkzeug.utils import secure_filename
from langdetect import detect, LangDetectException
import imghdr
import os
import requests


from flask import g
from flask_babel import get_locale
from PIL import Image

def n_height(o_height,o_width,n_width):
    x=(o_width*n_width)/o_height
    return x

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')
from flask import jsonify
from app.translate import translate

@app.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)
@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)
@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title='Explore', posts=posts.items,
                          next_url=next_url, prev_url=prev_url)
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    try:
        uploaded_file = request.files['post_img']
        filename=secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                    file_ext != validate_image(uploaded_file.stream):
                abort(400)
            filename = str(current_user.get_id()) + '_' + str(filename)
            uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], str(filename)))
    except:
        filename="wizard.jpg"

    if form.validate_on_submit():
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ''
        try:
            post_vid=form.post_vid.data
        except:
            post_vid ='https://www.youtube.com/embed/u4taz6dfPQc'

        post = Post(body=form.post.data, author=current_user,img_caption=form.img_caption.data,post_img=filename,language=language,post_vid=post_vid)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)

    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)




@app.before_request
def before_request():
    g.locale = str(get_locale())
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    img=User.profile_img(current_user)
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.tags = form.tags.data

        uploaded_file = request.files['profile_image']
        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                    file_ext != validate_image(uploaded_file.stream):
                abort(400)


            uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], current_user.get_id() + file_ext))
            current_user.profile_image = current_user.get_id() + file_ext

        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        form.tags.data = current_user.tags


    return render_template('edit_profile.html', title='Edit Profile',
                           form=form,img=img)

@app.route('/submit_style', methods=['GET', 'POST'])
@login_required
def submit_style():

    form = SubmitStyleForm(current_user.username,current_user.get_id())

    if form.validate_on_submit():

        style_nm=form.style_nm.data
        uploaded_file = request.files['nm']
        filename = secure_filename(uploaded_file.filename)
        try:
            language = detect(form.style_inspire.data)
        except LangDetectException:
            language = ''

        if filename != '' :
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                    file_ext != validate_image(uploaded_file.stream):
                abort(400)
            img_nm= str(current_user.id) + '_style_' + style_nm
            image = Image.open(uploaded_file)
            width, height = image.size
            rat = float(width) / float(height)
            xl = 2400
            lg = 1200
            med = 990
            sm = 760
            if rat > 1.34:
                img_rat = 'pan'
            elif rat > 1.05:
                img_rat = 'ls'
            elif rat < .95:
                img_rat = 'pt'
            else:
                img_rat = 'sq'
            out_dict = {}
            sz_lst = {'xl': xl, 'lg': lg, 'med': med, 'sm': sm}
            for key,value in sz_lst.items():
                new_width = value
                img_input = key
                new_height = int((xl * width) / int(height))
                new_size = (int(new_width), int(new_height))
                image.resize(new_size)
                img_db_nm=str(img_nm) +'_'+ str(img_rat)
                img_name = img_db_nm +'_'+ str(img_input) + str(file_ext)
                image.save(os.path.join(app.config['UPLOAD_PATH'], img_name))
            filename_pan=''
            filename_ls = ''
            filename_sq = ''
            filename_pt = ''
            if img_rat=='pan':
                filename_pan=img_db_nm
            elif img_rat=='ls':
                filename_ls=img_db_nm
            elif img_rat=='sq':
                filename_sq=img_db_nm
            elif img_rat=='pt':
                filename_pt=img_db_nm


        # Check if a record with the same style_nm and stylist already exists
        stylist = User.query.filter_by(username=current_user.id).first()
        style = Style.query.filter_by(style_nm=form.style_nm.data, stylist=stylist).first()
        if style:
            # If the record exists, update its attributes
            if img_rat=='pan':
                style.pan_color = form.color.data
                style.pan_nm = filename_pan
            if img_rat=='ls':
                style.ls_color = form.color.data
                style.ls_nm = filename_ls
            if img_rat=='sq':
                style.sq_color = form.color.data
                style.sq_nm = filename_sq
            if img_rat=='pt':
                style.pt_color = form.color.data
                style.pt_nm = filename_pt
            style.timestamp = datetime.utcnow
            style.style_inspire = form.style_inspire.data
            style.style_nm = form.style_nm.data
            style.language=language

        else:
            # If the record doesn't exist, create a new record
            if img_rat=='pan':
                style = Style(style_nm=form.style_nm.data, stylist=current_user, pan_color=form.color.data, pan_nm=filename_pan,style_inspire = form.style_inspire.data,language=language)
                db.session.add(style)
            if img_rat=='ls':
                style = Style(style_nm=form.style_nm.data, stylist=current_user,ls_color=form.color.data, ls_nm=filename_ls,style_inspire = form.style_inspire.data,language=language)
                db.session.add(style)
            if img_rat=='sq':
                style = Style(style_nm=form.style_nm.data, stylist=current_user, sq_color=form.color.data, sq_nm=filename_sq,style_inspire = form.style_inspire.data,language=language)
                db.session.add(style)
            if img_rat=='pt':
                style = Style(style_nm=form.style_nm.data, stylist=current_user, pt_color=form.color.data,pt_nm=filename_pt,style_inspire = form.style_inspire.data,language=language)
                db.session.add(style)

        # Commit the changes to the database
        db.session.commit()
        flash('Your style is now live!')
        return redirect(url_for('submit_style'))
    elif request.method == 'GET':
        stylist = User.query.filter_by(username=current_user.id).first()
        style = Style.query.filter_by(style_nm=form.style_nm.data, stylist=stylist).first()
        page = request.args.get('page', 1, type=int)

        styles = current_user.followed_styles().paginate(
            page=page, per_page=3, error_out=False)

        next_url = url_for('submit_style', page=styles.next_num) \
            if styles.has_next else None
        prev_url = url_for('submit_style', page=styles.prev_num) \
            if styles.has_prev else None
        return render_template('submit_style.html', title='Home', form=form,
                               styles=styles.items, next_url=next_url,
                               prev_url=prev_url)

    return render_template('submit_style.html', title='Add Style',
                           form=form, )


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))