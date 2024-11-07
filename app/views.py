import hashlib
import os
import re
import time
from datetime import datetime
from functools import wraps

from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from pony.orm import commit, db_session, desc

from app import app
from app.forms import PostForm, RegistrationForm, SettingsForm, TaskForm
from models import Users
from . import utils


@app.route('/')
@app.route('/index')
@app.route('/home')
def index():
    return render_template('home.html', current_user=current_user)


@app.route('/profile')
def profile():
    return redirect(url_for('profile'))


@app.route('/auth', methods=['POST'])
def auth_menu():
    login = request.form.get('login')
    password = request.form.get('password')

    user = Users.get(login=login)
    if user:
        flash('Пользователь с таким логином уже существует', 'alert info')
    else:
        if utils.hash_password(password) == user.hash_password:
            login_user(user, remember=True)
        else:
            flash('Пароль или логин неверны', 'alert error')

    return redirect(url_for('profile'))


@app.route('/reg', methods=['POST'])
def reg_menu():
    login = request.form.get('login')
    password = request.form.get('password')
    get_hash_password = utils.hash_password(password)

    user = Users.get(login=login)
    if user:
        flash('Данный пользователь уже существует', '')
    else:
        with db_session:
            Users(login=login, hash_password=get_hash_password)
            commit()

        return redirect(url_for('auth'))

    return redirect(url_for('reg'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта', 'alert success')
    return redirect(url_for('home'))
