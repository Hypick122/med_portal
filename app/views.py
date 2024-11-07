import os
import re
import time
from datetime import datetime
from functools import wraps

import vk_api
from dateutil import parser
from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from pony.orm import commit, db_session, desc
from twocaptcha import TwoCaptcha

from app import app
from app.forms import PostForm, RegistrationForm, SettingsForm, TaskForm
from models import Configs, Tasks, Users
from .utils import allowed_file

raw_date = {
    'day': 1,
    'week': 7,
    'month': 30,
    'year': 365,
    'indefinite': 0
}


@app.before_request
def verification_key_validity():
    if current_user.is_authenticated and current_user.expiry and current_user.expiry <= int(time.time()):
        logout_user()
        flash('Ваш ключ истек', 'alert info')
        return redirect(url_for('profile'))


def check_user_status_and_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.status in ["none", "not verified"]:
            flash('Ваш профиль еще не проверен', 'alert error')
            return redirect(session['previous_url'])

        if not current_user.token:
            flash('Добавьте токен от аккаунта вк во вкладке "Профиль"', 'alert error')
            return redirect(session['previous_url'])

        return func(*args, **kwargs)

    return wrapper


def fetch_vk_groups():
    if current_user.token:
        try:
            vk_session = vk_api.VkApi(token=current_user.token)
            api = vk_session.get_api()
            groups = api.groups.get(user_id=api.users.get()[0]["id"], filter=["admin", "editor"], extended=1)
        except vk_api.exceptions.ApiError as e:
            if e.code in [5, 1116]:
                current_user.token = ""
                flash(f'Токен от ВК недействителен', 'alert error')
                return redirect(url_for('repost'))

            flash(f'Произошла ошибка: {e}', 'alert error')
            return redirect(url_for('repost'))

        return locals().get('groups', [])


def update_form_from_config(form):
    kwargs = {}
    config = Configs.get(user_id=current_user.id, id=request.args.get('config'))
    if config:
        form.text_post.data = config.params["text"]
        form.name_task.data = config.name
        form.links.data = config.params["links"]

        kwargs.setdefault('config_groups', config.params["to_groups"])
        if config.params["links_select"]:
            kwargs.setdefault('config_links_select', config.params["links_select"])

        if config.params["date_public_post"]:
            form.date_public_post.data = datetime.fromtimestamp(config.params["date_public_post"])
        if config.params["date_delete_post"]:
            form.date_delete_post.data = datetime.fromtimestamp(config.params["date_delete_post"])

    return form, kwargs


def parse_date(date):
    return int(parser.parse(date).timestamp()) if date else 0


@app.route('/')
@app.route('/index')
@app.route('/home')
def index():
    return render_template('home.html', current_user=current_user)


@app.route('/repost')
def repost():
    form = PostForm()

    if not current_user.is_authenticated:
        return render_template('repost.html', groups=[], form=form)

    form, kwargs = update_form_from_config(form)

    session['previous_url'] = "repost"
    return render_template(
        'repost.html',
        groups=fetch_vk_groups(),
        current_user=current_user,
        configs=Configs.select(user_id=current_user.id).order_by(desc(Configs.id)),
        form=form,
        **kwargs,
    )


@app.route('/post')
def post():
    form = PostForm()

    if not current_user.is_authenticated:
        return render_template('post.html', groups=[], form=form)

    form, kwargs = update_form_from_config(form)

    session['previous_url'] = "post"
    return render_template(
        'post.html',
        groups=fetch_vk_groups(),
        configs=Configs.select(user_id=current_user.id).order_by(desc(Configs.id)),
        form=form,
        **kwargs,
    )


@app.route("/upload", methods=["POST"])
@login_required
@check_user_status_and_token
def upload():
    vk_session = vk_api.VkApi(token=current_user.token)
    api = vk_session.get_api()

    task_type = "ad" if session['previous_url'] == "repost" else "common"
    date_public_post = request.form.get('date_public_post')
    date_delete_post = request.form.get('date_delete_post')
    groups_select = request.form.getlist('group-select')

    attachments = request.form.get('objects')
    links = request.form.get('links')
    links_select = request.form.getlist('links-select')

    if not groups_select:
        flash(f"Нужно выбрать хотя бы одну группу", "alert error")
        return redirect(session['previous_url'])

    files_list = []
    if session['previous_url'] == "post":
        files = request.files.getlist("file")

        for file in files:
            if not allowed_file(file.filename):
                flash(f"Нельзя загрузить файл {file.filename}", "alert error")
                return redirect(session['previous_url'])

            elif file.filename:
                filename = f"{int(time.time())}_{file.filename}"

                files_list.append(filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    elif session['previous_url'] == "repost":
        if links:
            links = links.replace(" ", "").split(",")
            links_select.extend(links)

        for link in links_select:
            match = re.search(r"-(\d+)_\d+", link)
            if not match or not api.wall.getById(posts=match.group()):
                flash(f"Проблема с ссылкой", "alert error")
                return redirect(session['previous_url'])

            if links not in current_user.links:
                current_user.links.append(link)

    if attachments:
        attachments = attachments.replace(" ", "").split(",")

    groups = api.groups.getById(group_ids=list(map(int, groups_select)))
    groups_dict = {group["id"]: {"name": group["name"], "photo_50": group["photo_50"]} for group in groups}

    Tasks(
        name=request.form.get('name_task'),
        user_id=current_user.id,
        params={
            "type": task_type,
            "links": links_select,
            "text": request.form.get('text_post'),
            "files": files_list,
            "attachments": attachments,
            "source": request.form.get('source'),
            "to_groups": groups_dict,
            "posts": [],
            "logs": [],
        },
        changes={
            "create": {"date": parse_date(date_public_post), "is_done": False, "performed": False},
            "delete": {"date": parse_date(date_delete_post), "is_done": False, "performed": False},
            "fatal": False
        })
    commit()

    flash(f"Заявка добавлена в очередь", "alert info")
    return redirect(session['previous_url'])


@app.route("/delete/links", methods=["POST"])
@login_required
def delete_links():
    links_select = request.form.getlist('links-select')

    if not links_select:
        flash(f"Вы не выбрали ни одной ссылки", "alert info")
        return redirect(url_for(session['previous_url']))

    for link in links_select:
        current_user.links.remove(link)

    flash(f"Выбранные ссылки удалены", "alert success")
    return redirect(url_for(session['previous_url']))


@app.route("/delete/links/all", methods=["POST"])
@login_required
def delete_links_all():
    current_user.links = []
    commit()

    flash(f"Все ссылки удалены", "alert success")
    return redirect(url_for(session['previous_url']))


@app.route("/config/load", methods=["POST"])
@login_required
def config_load():
    selected_config = request.form.get("select-config")

    if selected_config == "Выбрать конфиг":
        flash("Вы не выбрали конфига", "alert info")
    else:
        flash("Конфиг загружен", "alert success")
        return redirect(url_for(session['previous_url'], config=selected_config))

    return redirect(url_for(session['previous_url']))


@app.route("/config/save", methods=["POST"])
@login_required
@check_user_status_and_token
def config_save():
    name_task = request.form.get('name_task')
    date_public_post = request.form.get('date_public_post')
    date_delete_post = request.form.get('date_delete_post')

    if not name_task:
        flash(f"Нужно назвать конфиг", "alert error")
        return redirect(url_for(session['previous_url']))

    config = Configs(
        name=name_task,
        user_id=current_user.id,
        params={
            "text": request.form.get('text_post'),
            "date_public_post": parse_date(date_public_post),
            "date_delete_post": parse_date(date_delete_post),
            "to_groups": list(map(int, request.form.getlist('group-select'))),
            "links": request.form.get('links'),
            "links_select": request.form.getlist('links-select'),
            "attachments": request.form.get('objects'),
            "source": request.form.get('source'),
        }
    )
    commit()

    flash(f"Конфиг сохранен", "alert success")
    return redirect(url_for(session['previous_url'], config=config.id))


@app.route("/config/delete", methods=["POST"])
@login_required
def config_delete():
    selected_config = request.form.get("select-config")

    if selected_config == "Выбрать конфиг":
        flash(f"Вы не выбрали конфига", "alert info")
    else:
        try:
            Configs.get(id=selected_config).delete()
        except AttributeError:
            flash(f"Конфиг уже удален", "alert error")
        else:
            flash(f"Конфиг удален", "alert success")

    return redirect(url_for(session['previous_url']))


@app.route('/repost/tasks')
def repost_tasks():
    session['previous_url'] = "repost_tasks"
    return render_template(
        'tasks.html',
        tasks=Tasks.select(user_id=current_user.id).order_by(desc(Tasks.id)) if current_user.is_authenticated else [],
        datetime=datetime,
        task_type='ad',
        form=TaskForm(),
    )


@app.route('/post/tasks')
def post_tasks():
    session['previous_url'] = "post_tasks"
    return render_template(
        'tasks.html',
        tasks=Tasks.select(user_id=current_user.id).order_by(desc(Tasks.id)) if current_user.is_authenticated else [],
        datetime=datetime,
        task_type='common',
        form=TaskForm(),
    )


@app.route("/update/task", methods=["POST"])
@login_required
def update_task():
    select_action = request.form.get('select_action')
    date_delete_post = request.form.get('date_delete_post')
    tasks_form = request.form.getlist('task-select')

    if not tasks_form:
        flash(f"Нужно выбрать хотя бы одну задачу", "alert error")
        return redirect(url_for(session['previous_url']))

    for task_id in tasks_form:
        task = Tasks.get(id=int(task_id))

        if select_action == "publish":
            if task.changes["create"]["is_done"]:
                new_task = Tasks(
                    name=task.name,
                    user_id=task.user_id,
                    params=task.params,
                    changes={
                        "create": {"date": parse_date(request.form.get('date_public_post')), "is_done": False, "performed": False},
                        "delete": {"date": parse_date(date_delete_post), "is_done": False, "performed": False},
                        "fatal": False
                    })
                new_task.params["posts"] = []

                flash('Заявка повторяется', 'alert info')
                return redirect(url_for(session['previous_url']))

            task.changes["create"]["date"] = int(time.time())

        elif select_action == "delete":
            if not task.changes["create"]["is_done"]:
                flash(f'Задача {task.id} еще не выполнялась', 'alert error')
                return redirect(url_for(session['previous_url']))

            elif task.changes["delete"]["is_done"]:
                flash(f'Посты из задачи {task.id} уже удалены', 'alert error')
                return redirect(url_for(session['previous_url']))

            task.changes["delete"]["date"] = int(time.time()) if not date_delete_post else int(parser.parse(date_delete_post).timestamp())

    commit()

    flash(f"Заявка добавлена в очередь", "alert info")
    return redirect(url_for(session['previous_url']))


@app.route('/admin')
@login_required
def admin():
    if current_user.status != "admin":
        return redirect(url_for('home'))

    Users.select(lambda u: u.status == "none" and u.created_at + 3600 < time.time()).delete(bulk=True)

    return render_template(
        'admin.html',
        current_user=current_user,
        users=Users.select(lambda u: u.status == "not verified" or u.expiry <= int(time.time())).order_by(desc(Users.id))
    )


@app.route('/create', methods=['POST'])
def create():
    expiry = request.form.get('select-expiry')
    full_access = request.form.get('checkbox-full-access', "verified")

    with db_session:
        expiry = int(time.time()) + raw_date.get(expiry) * 86400 if raw_date.get(expiry) else 0
        new_user = Users(expiry=expiry, status=full_access)
        commit()

    flash(f'Ключ: {new_user.key}', "alert info")
    return redirect(url_for('admin'))


@app.route('/activate', methods=['POST'])
def activate():
    expiry = request.form.get('select-expiry-activate')
    users = request.form.getlist('user-select')

    with db_session:
        expiry = int(time.time()) + raw_date.get(expiry) * 86400 if raw_date.get(expiry) else 0
        for user in users:
            g_user = Users.get(id=user)
            g_user.expiry = expiry
            g_user.status = "verified"
        commit()

    flash(f'Вы активировали ключи', 'alert success')
    return redirect(url_for('admin'))


@app.route('/profile')
def profile():
    if current_user.is_authenticated and current_user.captcha_key:
        try:
            balance = TwoCaptcha(current_user.captcha_key).balance()
        except:
            current_user.captcha_key = ""
            commit()

            flash('API ключ недействительный', 'alert error')
            return redirect(url_for('profile'))

    return render_template(
        'profile.html',
        current_user=current_user,
        Users=Users,
        balance=getattr(locals(), 'balance', None),
        expiry_date=datetime.utcfromtimestamp(current_user.expiry).strftime('%H:%M %d.%m.%Y') if current_user.is_authenticated else None,
        form_reg=RegistrationForm(),
        form_set=SettingsForm()
    )


@app.route('/registration', methods=['POST'])
def registration():
    uuid = request.form.get('uuid')

    if uuid:
        try:
            user = Users.get(key=uuid)
            if user and user.expiry != 0 and user.expiry <= int(time.time()):
                flash('Ваш ключ истек', 'alert info')
            elif user and user.status != "none":
                login_user(user, remember=True)
            else:
                flash('Ключ не найден', 'alert error')
        except ValueError:
            flash('Ключ не найден', 'alert error')
    else:
        flash('Введите ключ', 'alert error')

    return redirect(url_for('profile'))


@app.route('/update/settings', methods=['POST'])
@login_required
def update_setting():
    user = Users.get(key=current_user.key)
    token = request.form.get('token')
    c_key = request.form.get('captcha_key')

    if not token and not c_key:
        flash('Введите параметры', 'alert error')

    try:
        if token:
            vk_api.VkApi(token=token).get_api().users.get()
            user.token = token
            flash('Параметры сохранены', 'alert success')
        if c_key:
            TwoCaptcha(c_key).balance()
            user.captcha_key = c_key
            flash('Параметры сохранены', 'alert success')
    except:
        flash('Введенный токен или API ключ недействительный', 'alert error')

    return redirect(url_for('profile'))


@app.route('/buy', methods=['POST'])
def buy():
    key = request.form.get('new_user')
    with db_session:
        user = Users.get(key=key)
        user.status = "not verified"
        commit()

    flash(f'Принято', 'alert success')
    return redirect(url_for('profile'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта', 'alert success')
    return redirect(url_for('profile'))
