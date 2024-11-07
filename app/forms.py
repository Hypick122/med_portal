from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


class LoginForm(FlaskForm):
    login = StringField("", render_kw={"placeholder": "Логин"})
    password = StringField("", render_kw={"placeholder": "Пароль"})

    submit = SubmitField("Войти", render_kw={"class": "sumbit-btn"})


class RegistrationForm(FlaskForm):
    login = StringField("Логин", render_kw={"placeholder": "Логин"})
    password = StringField("Пароль", render_kw={"placeholder": "Пароль"})

    submit = SubmitField("Зарегистритротваться", render_kw={"class": "sumbit-btn"})


class SearchForm(FlaskForm):
    inn = StringField("", render_kw={"placeholder": " "})

    submit = SubmitField("Найти", render_kw={"class": "sumbit-btn"})