#principal - all dependances into __init__ file

from recordclass import RecordClass
import bs4
from bs4 import BeautifulSoup
from bs4.element import Tag
import requests
import datetime
import abc
from abc import abstractmethod, ABCMeta, abstractproperty
import json
from json import JSONEncoder
import pathlib
from typing import Iterable
from dataclasses import dataclass, field, fields, Field, MISSING
import pydantic
import inspect
import string
import importlib
import re

from .errors import (
    FieldNotAvailable,
    InsertionFailure,
    NoUniqueID,
    NoFurtherRequired,
    UnrecognizableURLPage,
    StrategyFailure,
    StrategyNotDetected,
    WrongConfiguration
)

from .marks import (
    Extractor__Mark,
    AutoConfig__Mark
)


from .autoconfig import (
    AutoConfig,
    ConfigField
)

from .interface import (
    TreeviewInsertable,
    StrategiesKeepable,
    ExtractorsKeepable,
    EmptyContainerCreatable,
    MapKeepable
)

from .containers import (
    InputArgs, Strategy, Element
)

from ..parsers import (
    ConfigDependantParser,
    UseableParser__Mark
)

from .strategy import (
    StrategyMap,
    StrategyParserConfigurationManager,
    reload_strategy
)

