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

# import json
from datetime import date
import os
import sqlite3
# from datetime import date
# from itertools import combinations
from numbers import Number

# import numpy as np
from flask import current_app, g
from gviz_api import DataTable
from pandas import read_sql, to_datetime
from pandas.api.types import is_numeric_dtype, is_string_dtype
# from PySide2 import QtWidgets


def sql_to_data_table(table_name, data_types=None, null_value=None, replace_null_columns=()) -> DataTable:
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
    table_data = get_database().query(f'SELECT * FROM {table_name};')
    if null_value is not None:
        for column in replace_null_columns:
            table_data[column][table_data[column].copy().isnull()] = -1

    columns = {}
    date_columns = []
    for column in table_data.columns:
        data_type = data_types.get(column)
        if data_type == 'date':
            date_columns.append(column)
        elif data_type is None:
            column_data_type = table_data.dtypes[column]
            if is_numeric_dtype(column_data_type):
                data_type = 'number'
            elif is_string_dtype(column_data_type):
                data_type = 'string'
            else:
                raise RuntimeError(f'Unsupported data type for {column}')
        columns[column] = (data_type, column)
        table = DataTable(columns)
    
    for column in date_columns:
        table_data[column] = to_datetime(table_data[column]).fillna(date.today())
    table.LoadData(table_data.to_dict('index').values())

    return table.ToJSon()


class Database:
    def __init__(self, database_file_path):
        if not os.path.exists(database_file_path):
            raise FileExistsError(database_file_path)
        self._connection = sqlite3.connect(database_file_path, detect_types=sqlite3.PARSE_DECLTYPES)
        self._connection.row_factory = sqlite3.Row
        with current_app.open_resource('schema.sql') as file:
            self._connection.executescript(file.read().decode('utf8'))

    def execute_many_single(self, query, values):
        return [row[0] for row in self.cursor.execute(query, values).fetchall()]
    
    def execute_one_single(self, query, values):
        result = self.execute_many_single(query, values)
        if result:
            return result[0]
        return None

    def query(self, query):
        return read_sql(query, self._connection)

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

    def close(self):
        self._connection.close()


_DATABASE_KEY = 'database'

def get_database():
    if _DATABASE_KEY not in g:
        g.database = Database(current_app.config['DATABASE'])
    
    return g.database


def close_database(e=None):
    database = g.pop(_DATABASE_KEY, None)
    if database is not None:
        database.close()


def initialize_app(app):
    app.teardown_appcontext(close_database)

