# Copyright 2021
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import sqlite3
from datetime import date
from itertools import combinations

import numpy as np
import pandas as pd
from gviz_api import DataTable
from PySide2 import QtWidgets


def sql_to_data_table(table_name, data_types=None) -> DataTable:
    """Convert a SQL table to a google table.

    Parameters
    ----------
    table_name : str
        The name of the table.
    data_types : str
        The DataTable type.
    """
    if data_types is None:
        data_types = {}
    table_data = pd.read_sql_query(f'select * from {table_name};', database.connection)
    columns = {}
    date_columns = []
    for column in table_data.columns:
        data_type = data_types.get(column)
        if data_type == 'date':
            date_columns.append(column)
        elif data_type is None:
            if table_data.dtypes[column] == np.int64:
                data_type = 'number'
            else:
                data_type = 'string'
        columns[column] = (data_type, column)
        table = DataTable(columns)
    
    for column in date_columns:
        table_data[column] = pd.to_datetime(table_data[column]).fillna(date.today())
    table.LoadData(table_data.to_dict('index').values())

    return table


class Database:
    def __init__(self, database_file_path):
        if not os.path.exists(database_file_path):
            raise FileExistsError(database_file_path)
        self.connection = sqlite3.connect(database_file_path)
        self.cursor = self.connection.cursor()

    def execute_many_single(self, query, values):
        return [row[0] for row in self.cursor.execute(query, values).fetchall()]
    
    def execute_one_single(self, query, values):
        result = self.execute_many_single(query, values)
        if result:
            return result[0]
        return None

    def people(self):
        return self.cursor.execute('select * from people').fetchall()

    def name(self, person_id):
        return self.cursor.execute('select ifnull(firstfirstname,"") || " " || ifnull(firstname,"") || " " || ifnull(middlename,"") || " " || ifnull(lastname," ") from people where id = ?', [person_id]).fetchone()[0].lstrip()

    def wife(self, person_id):
        return self.execute_one_single('select id from people where husband = ?', [person_id])

    def husband(self, person_id):
        return self.execute_one_single('select id from people where wife = ?', [person_id])

    def children(self, parent=None, father=None, mother=None):
        if parent is not None:
            return self.execute_many_single('select id from people where father = ? or mother = ?', [parent] * 2)
        elif mother is None:
            return self.execute_many_single('select id from people where father = ?', [father])
        elif father is None:
            return self.execute_many_single('select id from people where mother = ?', [mother])
        return self.execute_many_single('select id from people where father = ? and mother = ?', [father, mother])

    def generation(self, parents):
        question_marks = ','.join(['?'] * len(parents))
        query = f'select id from people where father in ({question_marks}) or mother in ({question_marks})'
        return self.execute_many_single(query, parents + parents)


database_file_path = os.path.expanduser('family.db')
database = Database(database_file_path)

data = pd.read_sql_query('select * from people;', database.connection)

# Replace null values with -1 to indicate not specified.
for column in ['Husband', 'Wife', 'Father', 'Mother']:
    data[column][data[column].copy().isnull()] = -1
columns = {}
for column in data.columns:
    # if 'date' in column:
        # data_type = 'date'
    if data.dtypes[column] in ['O']:
        data_type = 'string'
    else:
        data_type = 'number'
    columns[column] = (data_type, column)

table = DataTable(columns)
table.LoadData(data.to_dict('index').values())

timelines = sql_to_data_table('stays', {'Start': 'date', 
                                        'End': 'date'})

locations = sql_to_data_table('locations')

with open('table.js', 'w') as output_file:
    code = f"""function loadFamilyData()
        {{
            {table.ToJSCode('familyTable')}
            return familyTable;
        }}

        function loadTimelines()
        {{
            {timelines.ToJSCode('timelines')}
            return timelines;
        }}

        function loadLocations()
        {{
            {locations.ToJSCode('locations')}
            return locations;
        }}"""
    output_file.write(code)
