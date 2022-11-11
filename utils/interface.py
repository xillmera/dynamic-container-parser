from . import (
    ABCMeta, abstractproperty, abstractmethod
)

class TreeviewInsertable(metaclass=ABCMeta):
    @property
    @abstractmethod
    def expand_fields(self):
        pass

class MapKeepable(metaclass=ABCMeta):
    map = abstractproperty()


class StrategiesKeepable(metaclass=ABCMeta):
    __strategies__ = abstractproperty()


class ExtractorsKeepable(metaclass=ABCMeta):
    __extractors__ = abstractproperty()


class EmptyContainerCreatable(metaclass=ABCMeta):
    element_type = abstractproperty()

    @classmethod
    def create_empty(cls):
        return cls() #должно поддерживать пустой инит