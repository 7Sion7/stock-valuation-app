from datetime import datetime
from flask import session, redirect
from functools import wraps
import json

import sqlite3

class DataBase:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS favourite_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                cap_price NUMERIC NOT NULL,
                average_annual_return INTEGER NOT NULL,
                percentual_annual_return TEXT NOT NULL,
                maximum_reasonable_price NUMERIC NOT NULL,
                current_price NUMERIC NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        self.conn.commit()

    def update(self, table, user_id, values):
        placeholders = ', '.join([f"{key} = ?" for key in values.keys()])
        query = f"UPDATE {table} SET {placeholders} WHERE user_id = ?"
        print(placeholders, query)
        self.cursor.execute(query, list(values.values()) + [user_id])
        self.conn.commit()
        print(f"Updated {table} for user {user_id}.")
        return
    
    def delete(self, table, user_id):
        query = f"DELETE FROM {table} WHERE user_id = ?"
        self.cursor.execute(query, (user_id,))
        self.conn.commit()
        print(f"Deleted records from {table} for user {user_id}.")
        return
    
    def delete_all(self, table):
        query = f"DELETE FROM {table}"
        self.cursor.execute(query)
        self.conn.commit()
        print(f"All records deleted from {table}.")
        return
    
    def insert(self, table, user_id, values):

        if 'dividends_history' in values:
            values['dividends_history'] = json.dumps(values['dividends_history'])
        columns = ', '.join(values.keys())
        placeholders = ', '.join(['?' for _ in values])
        query = f"INSERT INTO {table} ({columns}, user_id) VALUES ({placeholders}, ?)"

        # Convert user_id to a list before concatenating
        self.cursor.execute(query, list(values.values()) + [user_id])
        self.conn.commit()
        print(f"Inserted data into {table} for user {user_id}.")
        if 'dividends_history' in values:
            values['dividends_history'] = json.loads(values['dividends_history'])
        return
    
    def add(self, table, values):
        columns = ', '.join(values.keys())
        placeholders = ', '.join(['?' for _ in values])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        self.cursor.execute(query, list(values.values()))
        self.conn.commit()
        print(f"New data added to table: {table}")
        return
    
    def select(self, table, columns, where_conditions=None):
        columns_str = ', '.join(columns)
        
        query = f"SELECT {columns_str} FROM {table}"
        
        if where_conditions:
            where_clause = ' AND '.join(f"{key} = ?" for key in where_conditions.keys())
            query += f" WHERE {where_clause}"
            values = tuple(where_conditions.values())
        else:
            values = ()
        
        self.cursor.execute(query, values)
        return self.cursor.fetchone()

    def selectall(self, table, columns, where_conditions=None):
        columns_str = ', '.join(columns)
        
        query = f"SELECT {columns_str} FROM {table}"
        
        if where_conditions:
            where_clause = ' AND '.join(f"{key} = ?" for key in where_conditions.keys())
            query += f" WHERE {where_clause}"
            values = tuple(where_conditions.values())
        else:
            values = ()
        
        self.cursor.execute(query, values)

        return self.cursor.fetchall()

    def close_connection(self):
        self.conn.close()
        print("Connection closed.")

def init_db(db_name):
    db_instance = DataBase(db_name)
    db_instance.create_tables()
    return db_instance


def get_date_range(years_ago):
    current_year = datetime.now().year
    target_year = current_year - years_ago
    
    return target_year, current_year

def usd(value):
    """Format value as USD."""
    if value is None:
        return "$0.00"
    return f"${value:,.2f}"

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function
