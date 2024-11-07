import hashlib


def hash_password(text):
    m = hashlib.sha256()
    m.update(bytes(text))

    return m.hexdigest()