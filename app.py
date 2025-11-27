import os, sys
from email.policy import default
from pathlib import Path

from click import confirmation_option
from flask import Flask, render_template, request, flash, redirect, url_for
from markupsafe import escape
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

SQLALCHEMY_DATABASE_URI = 'sqlite:///' if sys.platform.startswith('win') else 'sqlite:////'
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI + str(Path(app.root_path) / 'data.db')
app.config['SECRET_KEY'] = 'dev'  # 等同于 app.secret_key = 'dev'


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(app, model_class=Base)


@app.route('/hello')
def hello():
    return '<h1>Hello World!</h1><img src="http://helloflask.com/totoro.gif">'


@app.route('/user/<name>')
def user_page(name):
    return f'User {escape(name)}'


@app.route('/', methods=['GET', 'POST'])
def index():
    # user = db.session.execute(select(User)).scalar()
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for('index'))
        title = request.form['title']
        year = request.form['year']
        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('index'))
        movie = Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Item added.')
        return redirect(url_for('index'))
    movies = db.session.execute(select(Movie)).scalars().all()
    return render_template('index.html', movies=movies)


from sqlalchemy import String, select, True_
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, logout_user, login_required, current_user


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20))
    username: Mapped[str] = mapped_column(String(20))
    password_hash: Mapped[str | None] = mapped_column(String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


class Movie(db.Model):
    __tablename__ = 'movie'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(60))
    year: Mapped[str] = mapped_column(String(4))


import click


@app.cli.command('init-db')
@click.option('--drop', is_flag=True, help='Create after drop.')
def init_database(drop):
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized the database.')


@app.cli.command()
def forge():
    db.drop_all()
    db.create_all()

    name = 'Grey Li'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]

    user = User(name=name, username='admin')
    user.set_password('helloflask.')
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)
    db.session.commit()
    click.echo('Done!')


@app.errorhandler(404)
def page_not_found(error):
    # user = db.session.execute(select(User)).scalar()
    return render_template('404.html')


@app.context_processor
def inject_user():
    user = db.session.execute(select(User)).scalar()
    return dict(user=user)


@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit_movie(movie_id):
    movie = db.get_or_404(Movie, movie_id)

    if request.method == 'POST':
        title = request.form['title'].strip()
        year = request.form['year'].strip()

        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit_movie', movie_id=movie_id))
        movie.title = title
        movie.year = year
        db.session.commit()
        flash('Item updated.')
        return redirect(url_for('index'))
    return render_template('edit.html', movie=movie)


@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required
def delete_movie(movie_id):
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('index'))


@app.cli.command()
@click.option('--username', prompt=True, help='The username to login as.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password to login as.')
def admin(username, password):
    db.create_all()

    user = db.session.execute(select(User)).scalar()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)
    db.session.commit()
    click.echo('Done!')


from flask_login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(User, int(user_id))
    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid inpt.')
            return redirect(url_for('login'))
        user = db.session.execute(select(User).filter_by(username=username)).scalar()
        if user is not None and user.validate_password(password):
            login_user(user)
            flash('login successful.')
            return redirect(url_for('index'))
        flash('Invalid username or password.')
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.')
    return redirect(url_for('index'))


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']
        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))
        current_user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))
    return render_template('settings.html')
