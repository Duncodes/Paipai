# -*- coding: UTF-8 -*-
from collections import OrderedDict
from .. sql import FyMySQL
from .pysql import Model

import sys, time

class Query(object):
    _instances = {}
    _inits     = {}

    def __new__(cls,  *args, **kwargs):
        if not cls._instances.has_key(args[0].__name__):
            cls._instances[args[0].__name__] = super(Query, cls).__new__(cls, *args, **kwargs)
        
        return cls._instances[args[0].__name__]

    def __init__(self, owner):
        self.mysql  = FyMySQL._instance.db 
        self.cursor = FyMySQL._instance.db.cursor()
        self.array  = False
        self.is_raw = False
        self.query  = ''
        self.sql_m  = ['NOW()']

        if not self._inits.has_key(owner.__name__):
            self._inits[owner.__name__] = True

            self.owner  = owner
            self.model  = Model(owner.__name__)
            self.column = self.model._c
            self.prefix = FyMySQL._instance.settings['prefix']
            self.table  = self.prefix+self.model.name
            self.fields = []
            self.links  = {}
            self.link   = ''
            self.group  = ''

            for c in self.model._c:
                if self.model._c[c].etype:
                    self.fields.append('{}.{}'.format(self.table, c))

            self.fields = ', '.join(self.fields)

            for c in self.model._c:
                if self.model._c[c].link:
                    obj = Query(self.model._c[c].obj)
                    self.links[obj.model.name] = self.model._c[c]

                    if not self.model._c[c].multiple:
                        self.fields += ', '+obj.fields
                        self.link   += ' LEFT JOIN {0} ON {0}.{1}_id={2}.{4}_{3}'.format(obj.table, obj.model.name, self.table, self.model._c[c].link, self.model.name)
                    else:
                        obj.fields = []
                        for col in obj.model._c:
                            if obj.model._c[col].etype and col != self.model._c[c].obj:
                                if self.model._c[c].multiple == 'meta':
                                    obj.fields.append('GROUP_CONCAT({0}.{1} ORDER BY {0}.{2}_key  DESC SEPARATOR "||") AS {1}'.format(obj.table, col, obj.model.name))
                                else:
                                    obj.fields.append('GROUP_CONCAT({0}.{1} ORDER BY {0}.{2}_id  DESC SEPARATOR "||") AS {1}'.format(obj.table, col, obj.model.name))

                        self.fields += ', '+', '.join(obj.fields)
                        self.link   += ' LEFT JOIN {0} ON {2}.{4}_id={0}.{3}'.format(obj.table, obj.model.name, self.table, self.model._c[c].link, self.model.name)
                    
                    self.group  = ' GROUP BY {0}.{1}_id '.format(self.table, self.model.name)  
                    self.link  += obj.link
                    self.links.update(obj.links)

    # Filters
    def order_by(self, field, order='DESC'):
        field = self.model.name + '_' + field 
        if self.column.has_key(field):
            self.query += ' ORDER BY {} {} '.format(field, order)
        return self

    def filter(self, **kwargs):
        operator = 'AND'

        array_where = []
        for key, value in kwargs.items():
            column_name = self.model.name+'_'+key
            if self.column.has_key(column_name):
                array_where.append(self.table+'.'+column_name+'='+self.column[column_name].escape(value))
            if key == 'operator' and value == 'OR':
                operator = value

        operator = ' {0} '.format(operator)
        where = operator.join(array_where)

        self.query = ('SELECT {0} FROM {1} {2} WHERE {3} {4} ').format(
            self.fields, self.table, self.link, where, self.group
        )

        return self

    def where(self, where):
        self.query = ('SELECT {0} FROM {1} {2} WHERE {3} {4} ').format(
            self.fields, self.table, self.link, where, self.group
        ).replace('_fields_', self.fields).replace('_table_', self.table)

        return self    

    def sql(self, query):
        self.query = query.replace('_fields_', self.fields).replace('_table_', self.table)
        return self

    def raw(self, query):
        self.is_raw = True
        self.sql(query)
        return self

    def select_all(self, array=False):
        self.array = array
        self.query = (
            'SELECT {0} FROM {1} {2} {3}'.format(
                self.fields, self.table, self.link, self.group
            )
        )
        return self

    # Exec
    def one(self, force_item=None):
        self.query += ' LIMIT 0,1'
        return self.result(force_item)

    def limit(self, limit=1, position=0, array=False):
        self.array = array
        self.query += ' LIMIT '+str(position)+','+str(limit)
        return self.result()    

    def all(self, array=False):
        self.array = array
        return self.result()

    # add/delete/update/replace
    def add(self, item):
        authorized_key       = []
        authorized_data      = []

        for key, value in item.__dict__.iteritems():
            column_name = self.model.name+'_'+key
            if self.column.has_key(column_name) and self.column[column_name].etype != None:
                authorized_key.append(column_name)
                authorized_data.append(self.column[column_name].escape(value))

        self.query = (
            'INSERT INTO {0} ({1}) VALUES({2})'.format(
                self.table, ', '.join(authorized_key), ', '.join(authorized_data)
            )
        )

        self.execute()
        id_item = self.mysql.insert_id()


        if item.__dict__.has_key('meta'):
            for key, value in item.meta.items():
                self.update_meta(str(id_item), key , value)

        self.mysql.commit()
        self.filter(id=id_item).one(item)

    def delete(self, item):
        self.query = (
            'DELETE FROM {0} WHERE {1}_id={2}'.format(
                self.table, self.model.name, self.column[self.model.name+'_id'].escape(item.id)
            )
        )

        self.execute()
        
        if item.__dict__.has_key('meta'):
            self.query = (
                'DELETE FROM {0}meta WHERE {1}meta_id_{1}={2}'.format(
                    self.table, self.model.name, self.column[self.model.name+'_id'].escape(item.id)
                )
            )

            self.execute()

        item = None

    def update(self, item):
        authorized_data = []
        authorized_multiples = []

        for key, value in item.__dict__.iteritems():
            column_name = self.model.name+'_'+key
            if self.column.has_key(column_name) and self.column[column_name].etype != None:
                authorized_data.append(column_name+'='+self.column[column_name].escape(value))

        self.query = (
            'UPDATE {0} SET {1} WHERE {2}_id={3}'.format(
                self.table, ', '.join(authorized_data), self.model.name, self.column[self.model.name+'_id'].escape(item.id)
            )
        )
        self.execute()
        
        if item.__dict__.has_key('meta'):
            for key, value in item.meta.items():
                self.update_meta(str(item.id), key , value)

        self.execute()
        self.mysql.commit()

    # special
    def count(self, **kwargs):
        self.filter(**kwargs)
        self.query = self.query.replace(self.fields, 'COUNT(distinct {}) as c').format(self.model.name+'_id').replace(self.group, '')
        self.execute()
        return self.cursor.fetchone()[0]

    def count_lines(self):
        self.query = self.query.replace(self.fields, 'COUNT(distinct {}) as c').format(self.model.name+'_id').replace(self.group, '').split('LIMIT')[0]
        self.execute()

        return self.cursor.fetchone()[0]

    def count_all(self):
        self.query = 'SELECT COUNT(*) as c FROM {0}'.format(self.table)
        self.execute()
        return self.cursor.fetchone()[0] 

    def exist(self, key, value, ignore=False):
        column_name = self.model.name+'_'+key
        add_ignore  = ''

        if ignore:
            add_ignore = ' AND {}_id != {}'.format(self.model.name, ignore)
        
        if self.column.has_key(column_name):
            self.query = (
                'SELECT {0}_id FROM {1} WHERE {2}={3} {4}'.format(
                    self.model.name, 
                    self.table, 
                    column_name, 
                    self.column[column_name].escape(value), 
                    add_ignore
                )
            )
            self.execute()
            return bool(self.cursor.fetchone())
        return False

    def get_all(self, array=False, order=''):
        self.array = array
        self.query = (
            'SELECT {0} FROM {1} {2} {3} {4}'.format(
                self.fields, self.table, self.link, self.group, order
            )
        )
        return self.result()

    def get(self, id_item):
        return self.filter(id=id_item).one()


    # Results
    def get_result(self, force_item=None, item=False, multiple = False):
        if not force_item:
            tmp = self.owner()
        else:
            tmp = force_item        

        cols = OrderedDict()
        for key, value in item.items():
            if self.model._c.has_key(key) and self.model._c[key].etype:
                if not multiple:
                    setattr(tmp, key.replace(self.model.name+'_', ''), self.column[key].python(value))
                else:
                    if value: 
                        cols[key] = value.split('||')

        if multiple == 'meta':
            tmps = {}
            if cols:
                i = 0
                for item in cols[self.model.name+'_key']:
                    tmps[item] = cols[self.model.name+'_value'][i]
                    i += 1

            return tmps

        if multiple == 'obj':
            tmps = []
            if cols:
                i = 0
                for item in cols[self.model.name+'_id']:
                    tmp = self.owner()
                    tmp.id = item
                    for key, value in cols.items():
                        setattr(tmp, key.replace(self.model.name+'_', ''), self.column[key].python(value[i]))
                    
                    tmps.append(tmp)
                    i += 1                            

            return tmps

        return tmp

    def result(self, force_item=None):
        self.execute()
        result = self.cursor.fetchall()
        rv = []
        cols = [d[0] for d in self.cursor.description]
        for i in result: rv.append(OrderedDict(zip(cols, i)))
        result = rv

        if self.is_raw:
            self.is_raw = False
            return result

        final  = []
        for item in result:
            if not force_item:
                tmp = self.owner()
            else:
                tmp = force_item

            for key, value in item.items():
                if self.model._c.has_key(key):
                    if self.model._c[key].etype:
                        setattr(tmp, key.replace(self.model.name+'_', ''), self.column[key].python(value))
                else:
                    tmp_key = key.split('_')[0]
                    link = self.links[tmp_key]
                    obj  = Query(link.obj)

                    if not link.multiple:
                        setattr(tmp, link.name.replace(self.model.name+'_', ''), obj.get_result(item=item))
                    else:
                         setattr(tmp, link.name.replace(self.model.name+'_', ''), obj.get_result(item=item, multiple=link.multiple))
            tmp.init()

            if len(result) == 1 and not self.array:
                return tmp

            final.append(tmp)
            del tmp

        return final

    # Utils
    def update_meta(self, id_item, key, value):
        if value not in self.sql_m:
            value = '"{}"'.format(FyMySQL._instance.db.escape_string(value))


        self.query = (
            'REPLACE INTO {0}meta ({1}meta_id_{1}, {1}meta_key, {1}meta_value) VALUES({2}, "{3}", {4})'.format(
                self.table, self.model.name, id_item, key, value
            )
        )


        self.execute()

    def execute(self):
        try:
            if FyMySQL._instance.settings['debug']: 
                start_time = time.time()
            self.cursor.execute(self.query)

            if FyMySQL._instance.settings['debug']: 
                the_time = time.time() - start_time

                FyMySQL._instance.queries['n'] += 1
                FyMySQL._instance.queries['t'] += the_time
                FyMySQL._instance.queries['d'].append({'q' : self.query, 't': the_time})
        except:
            print 'Error: '+str(sys.exc_info()[0])+') \nQuery: '+self.query+'' 
            print 'MySQL:  '+str(sys.exc_info()[1])
            