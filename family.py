from mimetypes import init
from multiprocessing import connection
import os
from re import T
import re
from datetime import datetime

from flask import Blueprint, Flask, render_template, request, url_for
from gviz_api import DataTable
from pandas import to_datetime

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

    def add_parents(person_id, connections=None):
        if connections is None:
            connections = []
        
        for parent_id in get_database().query('SELECT Father, Mother FROM people WHERE ID = ?', parameters=[person_id]).values[0]:
            if parent_id is None:
                continue
            parent_id = int(parent_id)
            connections.append([parent_id, person_id])
            
            connections = add_parents(parent_id, connections)
        
        return connections
        
    def create_node(person_id, parentID=None):
        file_path_image = url_for('static', filename=f'image/face/{person_id}.png')
        if not os.path.exists('.' + file_path_image):
            file_path_image = None
        return [(str(person_id), render_template('leaf.html', name=get_database().name(person_id), image=file_path_image)), 
                "" if parentID is None else str(parentID)]

    root_person_id = request.args.get('id', 0)
    
    connections = [(root_person_id, None)] + add_children(root_person_id)

    descendents = DataTable([('ID', 'string'),
                             ('parentID', 'string')])
    descendents.LoadData([create_node(*connection) for connection in connections])

    connections = [[root_person_id, None]] + add_parents(root_person_id)
    ancestors = DataTable([('ID', 'string'),
                           ('parentID', 'string')])                
    ancestors.LoadData([create_node(*connection) for connection in connections])

    stays = get_database().query('SELECT Location.City, Start, End FROM Stay INNER JOIN Location ON Location.ID = Stay.LocationID WHERE PersonID = ? ORDER BY Start', [root_person_id])
    for column in ['Start', 'End']:
        stays[column] = to_datetime(stays[column])
        stays.fillna(datetime.today(), inplace=True)
    timelines = DataTable([('city', 'string'), 
                           ('Start', 'date'), 
                           ('End', 'date')])
    timelines.LoadData(stays.values.tolist())

    return render_template('tree.html', descendents=descendents.ToJSon(), ancestors=ancestors.ToJSon(), timelines=timelines.ToJSon())


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

