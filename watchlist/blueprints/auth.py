from flask import Blueprint, request, flash, redirect, url_for, render_template
from flask_login import login_user, logout_user, login_required
from sqlalchemy import select

from watchlist.extensions import db
from watchlist.model import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid inpt.')
            return redirect(url_for('auth.login'))
        user = db.session.execute(select(User).filter_by(username=username)).scalar()
        if user is not None and user.validate_password(password):
            login_user(user)
            flash('login successful.')
            return redirect(url_for('main.index'))
        flash('Invalid username or password.')
        return redirect(url_for('auth.login'))
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.')
    return redirect(url_for('main.index'))




