import os
import secrets

import requests
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from db import init_db, db
from models import User, Post
from forms import RegisterForm, LoginForm, UpdateAccountForm, PostForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace_this_with_a_secure_random_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# initialize DB
init_db(app)

# setup login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)


@app.route('/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            author=form.author.data,
            description=form.description.data
        )
        db.session.add(post)
        db.session.commit()
        flash('Post added!', 'success')
        return redirect(url_for('index'))
    return render_template('add_post.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        # check if email exists
        existing = User.query.filter_by(email=form.email.data).first()
        if existing:
            flash('Email already registered. Please login.', 'warning')
            return redirect(url_for('login'))
        # create user
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful.', 'success')
            return redirect(url_for('index'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():

        if form.image.data:
            random_hex = secrets.token_hex(8)
            _, f_ext = os.path.splitext(form.image.data.filename)
            picture_fn = random_hex + f_ext
            picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
            form.image.data.save(picture_path)
            current_user.image = picture_fn

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Account updated!', 'success')
        return redirect(url_for('account'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template('account.html', form=form)


NEWS_API_KEY = "72b3848834e04f1a9462a4d1053ce0b8"


@app.route('/news')
def news():
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
    response = requests.get(url)

    news_data = None
    if response.status_code == 200:
        news_data = response.json()
    else:
        flash("Failed to fetch news.", "danger")

    return render_template('news.html', news=news_data)


if __name__ == '__main__':
    app.run(debug=True)
