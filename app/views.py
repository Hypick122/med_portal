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
from app.forms import LoginForm, RegistrationForm
from models import Users
from . import utils


@app.route('/')
@app.route('/index')
@app.route('/home')
def index():
    return render_template('index.html', current_user=current_user)


# @app.route('/profile')
# def profile():
#     return redirect(url_for('profile'))


@app.route('/login')
def login_menu():
    return render_template('login.html', form_login=LoginForm())


@app.route('/register')
def reg_menu():
    return render_template('register.html', form_reg=RegistrationForm())


@app.route('/login', methods=['POST'])
def login_post():
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


@app.route('/register', methods=['POST'])
def reg_post():
    form_reg = RegistrationForm()
    # login = request.form.get('login')
    # password = request.form.get('password')
    get_hash_password = utils.hash_password(form_reg.password.data)

    user = Users.get(login=form_reg.login.data)
    print(user)
    if user:
        flash('Данный пользователь уже существует', '')
    else:
        new_user = Users(login=form_reg.login, hash_password=get_hash_password)
        commit()
        return redirect(url_for('login_menu'))

    return redirect(url_for('login_menu'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта', 'alert success')
    return redirect(url_for('home'))
