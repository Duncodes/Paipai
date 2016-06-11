# -*- coding: UTF-8 -*-
from flask.ext.babel import lazy_gettext as gettext

messages = {
    'updated'   : gettext('Item updated'),
    'added'     : gettext('Item added'),
    'moved'     : gettext('Item moved'),
    'deleted'   : gettext('Item deleted')
}