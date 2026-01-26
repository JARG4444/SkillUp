from flask import Flask
from .extensions import db, migrate, login_manager
from .config import Config
from .routes.user import user
from .routes.post import post
from .routes.teacher import teacher
from .routes.course import course_bp
from .routes.sandbox import sandbox_bp
from dotenv import load_dotenv

load_dotenv()

def create_app(config_class = Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.register_blueprint(user)
    app.register_blueprint(post)
    app.register_blueprint(teacher)
    app.register_blueprint(course_bp)
    app.register_blueprint(sandbox_bp)
  
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    login_manager.login_view = 'user.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'
    login_manager.login_message_category = 'info'

    with app.app_context():
        db.create_all()

    return app