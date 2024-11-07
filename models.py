import time
import uuid

from flask_login import UserMixin
from pony.orm import Database, Json, Optional, PrimaryKey, Required, StrArray

db = Database()


class Users(db.Entity, UserMixin):
    id = PrimaryKey(int, auto=True)

    key = Required(uuid.UUID, default=uuid.uuid4)
    expiry = Required(int, size=64)

    token = Optional(str)
    captcha_key = Optional(str)

    links = Required(StrArray, default=[])

    status = Required(str, default="none")
    created_at = Required(int, size=64, default=int(time.time()))


class Tasks(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str, nullable=True)
    user_id = Required(int)

    params = Required(Json)
    changes = Required(Json)


class Configs(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str, nullable=True)
    user_id = Required(int)

    params = Required(Json)
