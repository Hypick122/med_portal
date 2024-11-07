import hashlib
import os
import re
import time
from datetime import datetime
from functools import wraps

import requests
from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from pony.orm import commit, db_session, desc

from app import app
from app.forms import LoginForm, RegistrationForm, SearchForm
from models import Users
from . import utils


@app.route('/')
@app.route('/index')
@app.route('/home')
def index():
    if current_user.is_authenticated:
        return render_template('index.html', current_user=current_user, form_search=SearchForm())
    else:
        return redirect(url_for('login_menu'))


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
    if utils.hash_password(password) == user.hash_password:
        login_user(user, remember=True)
    else:
        flash('Пароль или логин неверны', 'alert error')

    return redirect(url_for('index'))


@app.route('/register', methods=['POST'])
def reg_post():
    form_reg = RegistrationForm()
    # login = request.form.get('login')
    # password = request.form.get('password')
    get_hash_password = utils.hash_password(form_reg.password.data)

    user = Users.get(login=form_reg.login.data)
    if user:
        flash('Данный пользователь уже существует', '')
    else:
        Users(login=form_reg.login.data, hash_password=get_hash_password)
        commit()
        return redirect(url_for('login_menu'))

    return redirect(url_for('login_menu'))


@app.route('/index', methods=['POST'])
def index_post():
    inn = request.form.get('inn')

    url = 'https://api.gigdata.ru/api/v2/suggest/party'

    # Заголовки
    headers = {
        'accept': 'application/json',
        'authorization': 'a8fa7hy4qrtr5689onjk6eyow7lrju61kwb3o0du',
        'Content-Type': 'application/json'
    }

    data = {
        "locations_boost": [
            {"kladr_id": "77"}
        ],
        "query": "Магнит",
        "count": 5,
        "locations": [
            {"kladr_id": "77"}
        ],
        "restrict_value": False
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        flash('ИНН: ')
        print("Ответ получен успешно:")
        print(response.json())
    else:
        print(f"Ошибка: {response.status_code}")
        print(response.text)

    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта', 'alert success')
    return redirect(url_for('login_menu'))
