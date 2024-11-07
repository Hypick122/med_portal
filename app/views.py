from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from pony.orm import commit, db_session

from app import app
from app.forms import LoginForm, RegistrationForm, SearchForm
from models import Users
from . import utils


@app.route('/')
@app.route('/index')
@app.route('/home')
def index():
    if current_user.is_authenticated:
        return render_template('index.html', current_user=current_user, form_search=SearchForm(),
                               login=current_user.login)
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
    if not user:
        # flash('Пользователя не существует', 'alert error')
        return redirect(url_for('reg_menu'))
    if utils.hash_password(password) == user.hash_password:
        login_user(user, remember=True)
    else:
        flash('Пароль или логин неверны', 'alert error')
        return redirect(url_for('login_menu'))

    return redirect(url_for('index'))


@app.route('/register', methods=['POST'])
def reg_post():
    form_reg = RegistrationForm()
    get_hash_password = utils.hash_password(form_reg.password.data)

    user = Users.get(login=form_reg.login.data)
    if user:
        flash('Данный пользователь уже существует', 'alert error')
        return redirect(url_for('login_menu'))
    else:
        with db_session:
            Users(login=form_reg.login.data, hash_password=get_hash_password)
            commit()

        flash('Вы создали аккаунт!', 'alert info')
        return redirect(url_for('login_menu'))


@app.route('/index', methods=['POST'])
def index_post():
    name = request.form.get('inn')
    response = utils.get_company_by_name(name)
    if response.status_code == 200:
        try:
            json = response.json()
            flash(f'Наименование: {json['suggestions'][0]['value']}'
                  f'<br>ИНН: {json['suggestions'][0]['data']['inn']}'
                  f'<br>Адрес: {json['suggestions'][0]['data']['address']['value']}'
                  f'<br>Руководитель: {json['suggestions'][0]['data']['management']['name']}',
                  'alert info')
        except:
            flash(f"Компания не найдена", 'alert error')
    else:
        flash(f"Не доросли еще до ИНН", 'alert info')

    return redirect(url_for('index'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта', 'alert success')
    return redirect(url_for('login_menu'))
