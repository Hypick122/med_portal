import os

from dotenv import load_dotenv

load_dotenv()
app_dir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'SECRET_KEY'
    DB = {
        'provider': os.environ.get('DB_PROVIDER'),
        'user': os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD'),
        'host': os.environ.get('DB_HOST'),
        'database': os.environ.get('DB_DATABASE'),
    }
    SCHEDULER_API_ENABLED = True


class DevelopmentConfig(BaseConfig):
    DEBUG = True
