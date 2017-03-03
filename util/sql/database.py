import mysql.connector

from util import logger


class Database:
    def __init__(self, name, user='root', password='', host='127.0.0.1'):
        self.name = name
        self.user = user
        self.host = host

        cnx = mysql.connector.connect(
            user=user,
            password=password,
            host=host,
            database=name)

        self._connection = cnx
        self._cursor = cnx.cursor()

        logger.info("Opened connection to MySQL database: {}".format(self.name))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # --- Class Methods

    def _close_connection(self):
        self._connection.close()

    def _close_cursor(self):
        self._cursor.close()

    def close(self):
        self._close_connection()
        self._close_cursor()
        logger.info("Closed connection to MySQL database: {}".format(self.name))

    # --- Instance Methods

    def show_all(self, table):
        query = "SELECT * from {}".format(table)
        self._cursor.execute(query)

        for item in self._cursor:
            print item
