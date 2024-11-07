import hashlib


def hash_password(text):
    if isinstance(text, str):
        text = text.encode('utf-8')
    else:
        text = str(text).encode('utf-8')

    m = hashlib.sha256()
    m.update(text)

    return m.hexdigest()