from mimetypes import init
import os
from re import T
import re

from flask import Blueprint, Flask, render_template

from data import get_database, initialize_app, sql_to_data_table

home = Blueprint('home', __name__)


@home.route('/')
def list_people():
    people = get_database().query('SELECT FirstName, LastName FROM people ORDER BY LastName')

    return render_template('home.html', people=people.to_json(orient='records'))


@home.route('/tree')
def display_tree():
    family_data = sql_to_data_table('people', null_value=-1, replace_null_columns=['Husband', 'Wife', 'Father', 'Mother'])
    timelines = sql_to_data_table('stays', {'Start': 'date', 'End': 'date'})
    locations = sql_to_data_table('locations')

    return render_template('tree.html', family_data=family_data, locations=locations, timelines=timelines)


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

