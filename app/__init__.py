import os

from flask import Flask
from flask_apscheduler import APScheduler
from flask_login import LoginManager
from pony.flask import Pony
from pony.orm import db_session

from models import Users, db

app = Flask(__name__)
app.config.from_object(os.environ.get('FLASK_ENV') or 'config.BaseConfig')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'uploads/')

db.bind(**app.config['DB'])
db.generate_mapping(create_tables=True)

Pony(app)
login_manager = LoginManager(app)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


with db_session:
    if not bool(Users.select(key="c088b007-0240-417f-91bd-61b57ba62332")):
        Users(key="c088b007-0240-417f-91bd-61b57ba62332", expiry=0, status="admin")


@login_manager.user_loader
def load_user(user_id):
    return Users.get(id=user_id)


from . import background, forms, views
