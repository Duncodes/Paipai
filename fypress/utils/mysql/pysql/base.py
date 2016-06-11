# -*- coding: UTF-8 -*-
import pprint, sys, datetime, json
from .query import Query

"""
    Base
"""
class _property(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)(owner)

class Base(object):
    @_property
    @staticmethod
    def query(owner):
        return Query(owner)

    def init(self):
        pass

    def dump(self, r=False):
        final = pprint.pformat(self.__dict__, indent=4)

        if r:
            return final

        print(final)

    def std_object(self, ajson=False):
        if ajson:
            final = {}
            for key, value in self.__dict__.items():
                if isinstance(value, datetime.datetime):
                    final[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    final[key] = value
            return json.dumps(final, indent=4)
        else:
            return self.__dict__

    def __repr__(self):
        try:
            return '{0}#{1}'.format(self.__class__.__name__, self.id)
        except:
            return '{0}#None'.format(self.__class__.__name__)