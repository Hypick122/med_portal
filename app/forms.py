from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


class LoginForm(FlaskForm):
    login = StringField("Логин", render_kw={"placeholder": " "})
    password = StringField("Пароль", render_kw={"placeholder": " "})

    submit = SubmitField("Войти", render_kw={"class": "sumbit-btn"})


class RegistrationForm(FlaskForm):
    login = StringField("Логин", render_kw={"placeholder": " "})
    password = StringField("Пароль", render_kw={"placeholder": " "})

    submit = SubmitField("Зарегистритротваться", render_kw={"class": "sumbit-btn"})