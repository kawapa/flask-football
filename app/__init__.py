from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def configure_app(app):
    app.config["SECRET_KEY"] = "devkey"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)


def register_blueprints(app):
    from .auth.routes import auth
    from .main.routes import main
    from .matches.routes import matches
    from .players.routes import players

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(matches, url_prefix="/matches")
    app.register_blueprint(players)


@login_manager.user_loader
def load_user(user_id):
    from .models import User

    return db.session.get(User, int(user_id))


def create_app():
    app = Flask(__name__)

    configure_app(app)
    register_extensions(app)
    register_blueprints(app)

    with app.app_context():
        db.create_all()

    return app