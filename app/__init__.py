import os

from flask import Flask
from flask_login import LoginManager
from pony.flask import Pony
from pony.orm import db_session

from models import Users, db

app = Flask(__name__)
app.config.from_object(os.environ.get('FLASK_ENV') or 'config.BaseConfig')
app.config['DOC_FOLDER'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'docs/')

db.bind('sqlite', ':sharedmemory:')
# db.bind(**app.config['DB'])
db.generate_mapping(create_tables=True)

Pony(app)
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.get(id=user_id)


from . import forms, views
