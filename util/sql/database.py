import mysql.connector
from mysql.connector import ProgrammingError

from util import logger
from util.retries import retries


class Database:
    @retries(3, 20.0)
    def __init__(self, name, user='root', password='', host='127.0.0.1', port='3306'):
        self.name = name
        self.user = user
        self.host = host
        self.port = port

        self.test_mode = False

        cnx = mysql.connector.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=name)

        self._connection = cnx
        self._cursor = cnx.cursor()
        self.persistent_cursor = False

        logger.info("Opened connection to MySQL database: {}".format(self.name))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # --- Class Methods

    def _open_cursor(self):
        self._cursor = self._connection.cursor(buffered=True)

    def _close_connection(self):
        self._connection.close()

    def _close_cursor(self):
        self._cursor.close()

    def open_cursor(self):
        self._cursor = self._connection.cursor(buffered=True)
        self.persistent_cursor = True

    def close(self):
        self._close_connection()
        self._close_cursor()
        logger.info("Closed connection to MySQL database: {}".format(self.name))

    def close_cursor(self):
        self._cursor.close()
        self.persistent_cursor = False

    # --- Database methods

    def commit(self):
        self._connection.commit()

    def query_count(self, query):
        result = self.query_return(query)
        return result[0][0]

    def query_return(self, query):
        if not self.persistent_cursor: self._open_cursor()
        self._cursor.execute(query)
        result = self._cursor.fetchall()
        if not self.persistent_cursor: self._close_cursor()
        return result

    def query_return_dict(self, query):
        if not self.persistent_cursor: self._open_cursor()
        self._cursor.execute(query)
        desc = self._cursor.description
        column_names = [col[0] for col in desc]
        result = [dict(zip(column_names, row)) for row in self._cursor]
        if not self.persistent_cursor: self._close_cursor()
        return result

    def query_return_dict_lookup(self, query, key):
        result = self.query_return_dict(query)
        output = {r[key]: r for r in result}
        return output

    def query_return_dict_single(self, query):
        result = self.query_return_dict(query)
        if result:
            return result[0]
        else:
            return {}

    def query_set(self, query, params=()):
        if not self.test_mode:
            if not self.persistent_cursor: self._open_cursor()
            self._cursor.execute(query, params)
            if not self.persistent_cursor: self._close_cursor()
        else:
            pass

    def query_set_many(self, query, params=[]):
        if not self.test_mode:
            if not self.persistent_cursor: self._open_cursor()
            self._cursor.executemany(query, params)
            if not self.persistent_cursor: self._close_cursor()
        else:
            pass
