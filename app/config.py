import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):

    USER = os.environ.get('POSTGRES_USER' , 'jarg')
    PASSWORD = os.environ.get('POSTGRES_PASSWORD', '1234')
    HOST = os.environ.get('POSTGRES_HOST', '127.0.0.1')
    PORT = os.environ.get('POSTGRES_PORT', '5432')
    DB = os.environ.get('POSTGRES_DB' , 'mydb')

    SQLALCHEMY_DATABASE_URI = f'postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}'
    SECRET_KEY = 'hsbdalfb71296vf3o2fb3874fb8y3f20yfb823ybf2@'
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    SANDBOX_BASE = os.getenv("SANDBOX_BASE", "http://127.0.0.1:8000")
    SANDBOX_API_KEY = os.getenv("SANDBOX_API_KEY", "dev-secret-change-me")

    UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads/teachers')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  