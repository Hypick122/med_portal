import hashlib
import requests


def hash_password(text):
    text = str(text).encode('utf-8')
    m = hashlib.sha256()
    m.update(text)

    return m.hexdigest()


def get_company_by_name(name):
    url = 'https://api.gigdata.ru/api/v2/suggest/party'

    headers = {
        'accept': 'application/json',
        'authorization': 'a8fa7hy4qrtr5689onjk6eyow7lrju61kwb3o0du',
        'Content-Type': 'application/json'
    }

    data = {
        "locations_boost": [
            {"kladr_id": "77"}
        ],
        "query": f"{name}",
        "count": 5,
        "locations": [
            {"kladr_id": "77"}
        ],
        "restrict_value": False
    }

    return requests.post(url, headers=headers, json=data)
