from mimetypes import init
from multiprocessing import connection
import os
from re import T
import re

from flask import Blueprint, Flask, render_template, request
from gviz_api import DataTable

from data import get_database, initialize_app, sql_to_data_table

home = Blueprint('home', __name__)


@home.route('/')
def list_people():
    people = get_database().query('SELECT FirstName, LastName FROM people ORDER BY LastName')

    return render_template('home.html', people=people.to_json(orient='records'))


@home.route('/tree')
def display_tree():
    def add_children(parent_id, connections=None):
        if connections is None:
            connections = []

        for _, child in get_database().query('SELECT ID FROM people WHERE Father = ? OR Mother = ?', 
                                             parameters=[parent_id] * 2).iterrows():
        # for(const childID of childrenIDs)
        # {
        #     const fatherID = getFamilyTableValue(childID, columnIndexFather)
        #     const motherID = getFamilyTableValue(childID, columnIndexMother)
        #     if(fatherID >= 0 && motherID >= 0)
        #     {
        #         for(const id of [fatherID, motherID])
        #             if(!partnersIDs.hasOwnProperty(id))
        #                 partnersIDs[id] = new Set()
        #         partnersIDs[fatherID].add(motherID)
        #         partnersIDs[motherID].add(fatherID)
        #     }
            connections.append((int(child.ID), parent_id))
            connections = add_children(child.ID, connections)
        # }
        return connections

    def create_node(person_id, parentID=None):
        return [(str(person_id), render_template('leaf.html', name=get_database().name(person_id))), 
                "" if parentID is None else str(parentID)]

    root_person_id = request.args.get('id', 0)
    
    connections = [(root_person_id, None)] + add_children(root_person_id)

    family_data = DataTable([('ID', 'string'),
                             ('parentID', 'string')])
    people = [create_node(*connection) for connection in connections]
    family_data.LoadData(people);

    timelines = sql_to_data_table('stays', {'Start': 'date', 'End': 'date'})
    locations = sql_to_data_table('locations')

    return render_template('tree.html', family_data=family_data.ToJSon(), locations=locations, timelines=timelines)


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

