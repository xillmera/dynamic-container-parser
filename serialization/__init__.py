import json, pathlib

from .. import (
    Element,
    NoUniqueID, InsertionFailure,
    AutoConfig__Mark, ConfigField
)

#from .sqlitedb import SqliteDataBase
SqliteDataBase = object()

from .jsonfile import JSONSerialisation


class DbInteraction:
    @classmethod
    def save(cls, extractor: Element):
        SqliteDataBase.insert_element(extractor) #future


class FileInteraction:
    @classmethod
    def save(cls, element: Element):
        JSONSerialisation.serialize(element)