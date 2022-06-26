from mimetypes import init
import os
from re import T
import re
from flask import Blueprint, Flask, render_template
from data import get_database, initialize_app

home = Blueprint('home', __name__)

@home.route('/')
def list_people():
    database = get_database()
    people = database.query('SELECT FirstName, LastName FROM people ORDER BY LastName')

    return render_template('home.html', people=people.to_json(orient='records'))


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY='dev', DATABASE=os.path.join(app.instance_path, 'family.db'))

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    app.register_blueprint(home)

    initialize_app(app)

    return app

