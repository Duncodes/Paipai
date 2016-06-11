# -*- coding: UTF-8 -*-
from ..sql import FyMySQL as db

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

class FlaskFyMySQL(object):
    def __init__(self, app=None):
        self.app = app
        if self.app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('MYSQL_HOST', 'localhost')
        app.config.setdefault('MYSQL_USER', None)
        app.config.setdefault('MYSQL_PASSWORD', None)
        app.config.setdefault('MYSQL_DB', None)
        app.config.setdefault('MYSQL_PORT', 3306)
        app.config.setdefault('MYSQL_UNIX_SOCKET', None)
        app.config.setdefault('MYSQL_CONNECT_TIMEOUT', 10)
        app.config.setdefault('MYSQL_READ_DEFAULT_FILE', None)
        app.config.setdefault('MYSQL_USE_UNICODE', True)
        app.config.setdefault('MYSQL_CHARSET', 'utf8')
        app.config.setdefault('MYSQL_SQL_MODE', None)
        app.config.setdefault('MYSQL_CURSORCLASS', 'Cursor')
        app.config.setdefault('MYSQL_PREFIX', 'flask_')

        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

        self.connect()

    def connect(self):
        flask_to_mysql = {
            'MYSQL_HOST'                : 'host',
            'MYSQL_USER'                : 'user',
            'MYSQL_PASSWORD'            : 'passwd',
            'MYSQL_DB'                  : 'db',
            'MYSQL_PORT'                : 'port',
            'MYSQL_UNIX_SOCKET'         : 'unix_socket',
            'MYSQL_CONNECT_TIMEOUT'     : 'connect_timeout',
            'MYSQL_READ_DEFAULT_FILE'   : 'read_default_file',
            'MYSQL_USE_UNICODE'         : 'use_unicode',
            'MYSQL_CHARSET'             : 'charset',
            'MYSQL_SQL_MODE'            : 'sql_mode',
            'MYSQL_CURSORCLASS'         : 'cursorclass',
            'MYSQL_PREFIX'              : 'prefix',
            'DEBUG'                     : 'debug'
        }

        kwargs = {}

        for setting in flask_to_mysql:
            if self.app.config[setting]:
                kwargs[flask_to_mysql[setting]] = self.app.config[setting]

        self.db =  db(**kwargs) 
        return self.db

    def teardown(self, exception):
        self.db.disconnect()
