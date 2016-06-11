# -*- coding: UTF-8 -*-
from __future__ import unicode_literals
from unidecode import unidecode
from collections import OrderedDict

from .. sql import FyMySQL

import inspect, json, datetime

"""
    Column
"""
class Column(object):
    def __init__(self, **kwargs):
        self.primary_key = False
        self.foreign_key = []

        self.name        = unicode(inspect.stack()[1][4][0].strip().split("\t")[0].split(" ")[0].strip())
        self.model       = unicode(inspect.stack()[1][3].lower())

        _model           = Model(self.model)

        self.etype          = kwargs.pop('etype', None)
        self.primary_key    = kwargs.pop('primary_key', False)
        self.link           = kwargs.pop('link', False)
        self.obj            = kwargs.pop('obj', False)
        self.multiple       = kwargs.pop('multiple', False)

        if kwargs.has_key('foreign_key'):
            self.foreign_key.append(kwargs[foreign_key])

        if self.etype == 'datetime':
            self.datetime_format = '%Y-%m-%d %H:%M:%S'

        _model.add_column(self.name, self)

    def python(self, value):
        if self.etype == 'string' and not value:
            return ''
            
        if self.etype in ['string', 'json'] and value:
            value = value.decode('unicode_escape')

        if self.etype == 'json':
            if not value:
                return value

            return json.loads(value)

        if self.etype == 'string':
            return unicode(value)

        return value

    def escape(self, value):
        sql = ['NOW()']

        if value in sql:
            return value

        if value == None or value == 'None':
            return 'NULL'

        if self.etype == 'int':
            try:
                return str(int(value))
            except ValueError:
                return str(0)


        tmp = '"{}"'

        if self.etype in ['string', 'json']:
            if self.etype == 'json':
                value = json.dumps(value).encode('unicode_escape')
            value = value.encode('unicode_escape')

        if self.etype == 'string' and value not in sql:
            value = FyMySQL._instance.db.escape_string(value)
            return tmp.format(value)
        elif self.etype == 'datetime':
            return tmp.format(value)
        elif self.etype == 'json':
            if value:
                value = FyMySQL._instance.db.escape_string(value)
                return tmp.format(value)

        return unicode(value)

"""
    Model
"""
class Model(object):
    _instances = {}

    def __new__(cls,  *args, **kwargs):
        if not cls._instances.has_key(args[0].lower()):
            cls._instances[args[0].lower()] = super(Model, cls).__new__(cls)
            cls._instances[args[0].lower()].init(*args, **kwargs)

        return cls._instances[args[0].lower()]

    def init(self, name):
        self._c    = OrderedDict()
        self.links = []
        self.name  = name

    def add_column(self, key, value):
        self._c[key] = value


