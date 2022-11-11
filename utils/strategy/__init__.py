from .. import (
    re, importlib,
    json, pathlib, requests,
    BeautifulSoup, Tag,
    Strategy,
    FieldNotAvailable, StrategyFailure,
    AutoConfig__Mark, ConfigField, AutoConfig,
    Extractor__Mark,
    ABCMeta, abstractproperty,
    ConfigDependantParser, UseableParser__Mark,
    dataclass, string,
    StrategiesKeepable, ExtractorsKeepable, EmptyContainerCreatable,
    MapKeepable
)

#from . import map
#StrategyMap = map.StrategyMap
from .map import StrategyMap
from .manager import StrategyParserConfigurationManager

def reload_strategy():
    new_map = importlib.reload(map)
    for inst in MapKeepable.__subclasses__():
        inst.map = new_map.StrategyMap
    AutoConfig.deliver_initials()
