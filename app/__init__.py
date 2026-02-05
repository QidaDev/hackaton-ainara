import os

from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.db_connection import get_db


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)
    
    import app.db_connection as db_connection
    db_client = get_db(Config.mongo_connection_string)
    db_connection.db = db_client["ainara-db"]

    # ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    from app.routes import api_bp
    app.register_blueprint(api_bp)

    return app
