# -*- coding: UTF-8 -*-
import MySQLdb, MySQLdb.cursors

class FyMySQL(object):
    _instance = None
    _connect  = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FyMySQL, cls).__new__(cls, *args, **kwargs)

        return cls._instance

    def __init__(self, **kwargs):
        self.settings = {
            'host'              : 'localhost',
            'user'              : None,
            'passwd'            : None,
            'db'                : None,
            'port'              : 3306,
            'unix_socket'       : None,
            'connect_timeout'   : 10,
            'read_default_file' : None,
            'use_unicode'       : True,
            'charset'           : 'utf8',
            'sql_mode'          : None,
            'prefix'            : '',
            'debug'             : False,
            'cursorclass'       : 'Cursor'
        }

        self.queries      = {'n':0, 't':0., 'd':[]}

        self.mysql_kwargs = {}

        for setting, value in kwargs.items():
            if self.settings.has_key(setting):
                self.settings[setting] = value
                
                if setting != 'prefix' and setting != 'debug':
                    if setting == 'cursorclass':
                            self.mysql_kwargs[setting] = getattr(MySQLdb.cursors, value)
                            
                    elif value != None:
                        self.mysql_kwargs[setting] = value

        if not self.mysql_kwargs.has_key('cursorclass'):
            self.mysql_kwargs['cursorclass'] = getattr(MySQLdb.cursors, self.settings['cursorclass'])

    def test(self):
        return MySQLdb.connect(**self.mysql_kwargs)

    @property
    def db(self):
        if self._connect == None:
            self._connect =MySQLdb.connect(**self.mysql_kwargs)

        return self._connect

    @property
    def cursor(self):
        return self._connect.cursor()
    

    def disconnect(self):
        if self._connect != None:
            self.db.commit()
            self.db.close()
            if self.settings['debug']:
                self.queries = {'n':0, 't':0., 'd':[]}
            self._connect = None

