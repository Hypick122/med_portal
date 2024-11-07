from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, DateTimeLocalField


class PostForm(FlaskForm):
    text_post = TextAreaField()
    links = StringField("Ссылки на пост", render_kw={"placeholder": "https://vk.com/wall-213929265_4968"})
    objects = StringField("Обьекты", render_kw={"placeholder": "audio_playlist55494_15"})
    source = StringField("Источник", render_kw={"placeholder": "https://vk.com/superapp?w=wall-27902394_1112599"})

    name_task = StringField("Название задачи", render_kw={"placeholder": " "})
    date_public_post = DateTimeLocalField("Публикация по времени:", format="%Y-%m-%dT%H:%M")
    date_delete_post = DateTimeLocalField("Удаление по времени:", format="%Y-%m-%dT%H:%M")

    submit = SubmitField("Запустить", render_kw={"class": "sumbit-btn"})


class TaskForm(FlaskForm):
    select_action = SelectField(choices=[('publish', 'Опубликовать'), ('delete', 'Удалить опубликованные посты')])

    date_public_post = DateTimeLocalField("Публикация по времени:", format="%Y-%m-%dT%H:%M")
    date_delete_post = DateTimeLocalField("Удаление по времени:", format="%Y-%m-%dT%H:%M")

    submit = SubmitField("Выполнить", render_kw={"class": "sumbit-btn"})


class RegistrationForm(FlaskForm):
    uuid = StringField("Ключ", render_kw={"placeholder": " "})

    submit = SubmitField("Войти", render_kw={"class": "sumbit-btn"})


class SettingsForm(FlaskForm):
    token = StringField("Токен от аккаунта ВК", render_kw={"placeholder": " "})
    captcha_key = StringField("API ключ от аккаунта rucaptcha", render_kw={"placeholder": " "})

    submit = SubmitField("Сохранить", render_kw={"class": "sumbit-btn"})
