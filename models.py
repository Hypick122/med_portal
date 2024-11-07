import time
import uuid

from flask_login import UserMixin
from pony.orm import Database, Json, Optional, PrimaryKey, Required, StrArray

db = Database()


class Users(db.Entity, UserMixin):
    id = PrimaryKey(int, auto=True)

    login = Required(str)
    hash_password = Required(str)


class Documents(db.Entity):
    id = PrimaryKey(int, auto=True)
    user_id = Required(int)
