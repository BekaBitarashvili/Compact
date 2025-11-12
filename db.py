from flask_sqlalchemy import SQLAlchemy


# create SQLAlchemy instance to import into app and models
db = SQLAlchemy()


def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()