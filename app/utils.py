import os

from twocaptcha import TwoCaptcha


def allowed_file(filename):
    extension = os.path.splitext(filename)[1]
    return extension not in [".mp3", ".exe", ".bat", ".com", ".cmd", ".msi", ".jar"]


def captcha_handler(captcha, api_key):
    if api_key:
        solver = TwoCaptcha(api_key)

        result = solver.normal(captcha.get_url())
        return captcha.try_again(result["code"])

    return None
