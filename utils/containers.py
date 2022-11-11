from . import (
    pydantic,
    dataclass, field, fields, Field, MISSING,
    Tag,
    TreeviewInsertable,
    StrategyFailure,
    string, EmptyContainerCreatable
)

class SizedField(Field):
    def __init__(self, size=0.0, **kw):
        args_alias = {
            'default':MISSING,
            'default_factory':MISSING,
            'init':True,
            'repr':True,
            'hash':None,
            'compare':True,
            'metadata':None,
            'kw_only':MISSING
        }
        args_alias.update(kw)
        super().__init__(**args_alias)
        self.size = size

class InputArgs(pydantic.BaseModel):
    url: str = pydantic.Field(description="Ссылка на целевую страницу")
    additional_test_request: bool = pydantic.Field(default=False, description="Дополнительно проверяет полученный контент при выборе парсера")#, alias='test-request')
    js_render: bool = pydantic.Field(default=False, description="При парсинге рендерит страницу как в браузере")
    db_save: bool = pydantic.Field(default=True, description="Без сохранения данных в базу")
    json_save: bool = pydantic.Field(default=False, description="Cохраняет вывод парсера в формате json в папку указанную в config")
    st_el: int | None = None
    ed_el: int | None = None

@dataclass
class Strategy(TreeviewInsertable, EmptyContainerCreatable):
    is_value: bool = False
    events: str | list[str] = field(default_factory=list) #not ! list[list[str]]
    config_sequence: str | list[str] = field(default_factory=list)
    initial: str | list[str] = field(default_factory=list)
    is_cashed: bool = False
    is_gen: bool = False
    default: any = None
    context: dict = field(default_factory=dict)
    return_key: str = 'res'
    description: str = None

    element_type = None

    def duplicate(self):
        return self.__class__(**self.asdict())

    @staticmethod
    def _argument_parser(argument_sequence: list[str] | str | None):
        if argument_sequence is None:
            return []
        if not isinstance(argument_sequence, list):
            argument_sequence = argument_sequence.split(',')
        elif len(argument_sequence) == 0 :
            return []
        if not isinstance(argument_sequence[0], list) and False: #dep
            # line in treeview must be str
            argument_sequence = [
                i.split('.')
                for i
                in argument_sequence
            ]
        return argument_sequence

    @classmethod
    def fromdict(cls, input:dict) -> 'Strategy':
        """Last formatting used. Also conversion.
        All data input is str or iterable str arrays but there are bool values"""
        sub_dict = {
            key:cls._argument_parser(input.get(key, None))
            for key in cls.parseable_fields
        }
        result = dict(input)
        result.update(sub_dict)
        for key in result:
            if result[key] == 'None':
                result[key] = None
        for key in cls.bool_fields: #convertion
            if key not in result:
                continue
            val = None
            test_val = result[key]
            if test_val is None:
                val = None
            elif not isinstance(test_val, bool):
                assert isinstance(test_val, str), f'ManualError: Not string or bool ({type(test_val)}) is unacceptable for bool field'
                match result[key]:
                    case 'True':
                        val = True
                    case 'False':
                        val = False
                    case _:
                        val = None
            else :
                val = test_val
            result[key] = val
        return cls(**result)

    def asdict(self):
        # сохраняет только те поля что были изменены
        repr = dict()
        for name, field_obj in self.__dataclass_fields__.items():
            is_not_default_value = (value := getattr(self, name, (default := field_obj.default))) != default
            try:
                is_not_empty_factory = not (isinstance(value, field_obj.default_factory) and len(value) == 0)
            except TypeError:
                #default_factory is missing type  (<dataclasses._MISSING_TYPE object at ---)
                is_not_empty_factory = True
            if is_not_default_value and is_not_empty_factory:
                repr[name] = value #\ #list[list[str]] fixer
                    #if name not in self.parseable_fields else ['.'.join(i) for i in value]
        return repr

    @classmethod
    def is_valid(cls, input_: 'Strategy') -> bool:
        validation_sequence = [
            *[val is not None and isinstance(val, bool) for val in [getattr(input_, key) for key in cls.bool_fields]],
            *[cls.EventConfiguration.is_acceptable(line) for line in input_.events],
            *[cls.AliasConfiguration.is_acceptable(line) for line in input_.initial],
            *[cls.StepConfiguration.is_acceptable(line) for line in input_.config_sequence]
            #dict - any
        ]
        print(validation_sequence)
        return all(validation_sequence)

    @dataclass(init=True)
    class AliasConfiguration:
        base_attr: str
        alias: str

        @classmethod
        def is_acceptable(cls, line:str) -> bool:
            try:
                assert line.count('.') == 1,  f'line ({line}) - has more than one dot'
                acceptable_charset= set(string.ascii_letters + '_')
                symbols_in_parts = [set(i) for i in line.split('.')]
                for symbol_part in symbols_in_parts:
                    diff = symbol_part.difference(acceptable_charset)
                    check = len(diff) == 0
                    assert check, f'line ({line}) - has wrong symbols ({diff})'
                return True
            except AssertionError as err:
                print('AliasConf.is_acceptable: ', err)
                return False

        @classmethod
        def fromline(cls, line:str) -> 'AliasConfiguration':
            parts = line.split('.')
            return cls(*parts)


    @dataclass(init=True)
    class EventConfiguration:
        target_attr: str
        name: str

        @classmethod
        def is_acceptable(cls, line:str) -> bool:
            try:
                assert line.count('.') == 1,  f'line ({line}) - has more than one dot'
                acceptable_charset= set(string.ascii_letters + '_')
                symbols_in_parts = [set(i) for i in line.split('.')]
                for symbol_part in symbols_in_parts:
                    diff = symbol_part.difference(acceptable_charset)
                    check = len(diff) == 0
                    assert check, f'line ({line}) - has wrong symbols ({diff})'
                return True
            except AssertionError as err:
                print('EventConf.is_acceptable: ', err)
                return False

        @classmethod
        def fromline(cls, line:str) -> 'EventConfiguration':
            parts = line.split('.')
            return cls(*parts)

    @classmethod
    def set__is_test_configuration(cls, value: bool):
        cls.StepConfiguration.ignore_test_conf = not value

    @dataclass
    class StepConfiguration:
        type_: str = None
        name: str = None
        return_subkey: str = None
        is_stop: bool = False
        is_test: bool = False
        proxy_items: list[tuple[str, str]] | None = None
        foreach_subkey: str | None = None
        target_subkey: str | None = None

        ignore_test_conf = True
        @classmethod
        def is_acceptable(cls, line: str) -> bool:
            try:
                if line == 'end':
                    print(line=='end')
                    return True
                acceptable_charset= string.ascii_letters + string.digits + '@!_.>'
                if '>' in line:
                    assert line.index('>') == 0, 'test sequence delimeter is placed wrong (only first symb)'
                assert all([letter in acceptable_charset for letter in line])
                assert len(line) != 0, 'empty_line'
                assert line.count('.') >= 2, 'not enought separators (dots)'
                return True
            except AssertionError as err:
                print(err)
                return False

        @classmethod
        def fromline(cls, line: str) -> 'StepConfiguration':
            """fabric"""
            # possible StrategyMap Methods Check. (if mark to engine classes extracted form mapper)
            if not cls.is_acceptable(line= line):
                raise ValueError('Line has wrong format')
            if line == 'end':
                return cls(is_stop =True)

            is_test = line.startswith('>')
            if is_test:
                line = line[1:]
            if not cls.ignore_test_conf:
                is_test = False

            type_, name, return_subkey = line.split('.')
            foreach_subkey = target_subkey = None
            proxy_items = None
            if '@' in name:
                name, *additional = name.split('@')
                if name.count('@') % 2 != 0:
                    raise StrategyFailure('Wrong rename usage')
                proxy_items = list(zip(additional[::2], additional[1::2]))
            if '!' in name and name.count('!') == 2:
                name, foreach_subkey, target_subkey = name.split('!')
            return cls(
                type_=type_,
                name=name,
                is_test = is_test,
                return_subkey=return_subkey,
                proxy_items=proxy_items,
                foreach_subkey=foreach_subkey,
                target_subkey=target_subkey
            )

    def _proxy_iterator(self, iterable_, split_method) -> StepConfiguration | AliasConfiguration | StrategyFailure:
        for line in iterable_:
            try:
                yield split_method(line)
            except ValueError:
                raise StrategyFailure(f'Wrong configuration line "{line}"')

    def getattr_iter(self, attr_name):
        value = getattr(self, attr_name)
        if attr_name in self.parseable_fields:
            iterable_ = value
            match attr_name:
                case 'config_sequence':
                    split_method = self.StepConfiguration.fromline
                case 'events':
                    split_method = self.EventConfiguration.fromline
                case _:
                    split_method = self.AliasConfiguration.fromline
            return (split_method(i) for i in iterable_)
        return value

    @classmethod
    @property
    def value_repr_keys(cls):
        return ('is_value', 'default', 'description')

    @classmethod
    @property
    def bool_fields(cls):
        return ('is_value', 'is_cashed', 'is_gen')

    @classmethod
    @property
    def parseable_fields(cls):
        return ('events', 'config_sequence', 'initial')

    @classmethod
    @property
    def expand_fields(cls):
        return ('events', 'config_sequence', 'initial', 'context')


@dataclass
class Element:
    url__secondary_page: str = SizedField(default=None, size=1)

    _sizes_collector = []

    @classmethod
    def compute_unify_sizes(cls):
        amount = len(cls._sizes_collector)
        if amount == 0:
            return
        sum = amount #единичные показатели
        sum_sizes = dict()
        for sizes in cls._sizes_collector:
            for key, value in sizes.items():
                if key not in sum_sizes:
                    sum_sizes[key] = value
                else :
                    sum_sizes[key] += value
        for key in sum_sizes:
            if sum_sizes[key] is None:
                sum_sizes[key] = None
            else:
                sum_sizes[key] /= amount
        return sum_sizes

    @classmethod
    def set_sizes(cls, sizes: dict):
        for name, field_obj in cls.__dataclass_fields__.items():
            field_obj.size = sizes[name]

    def asdict__different(self):
        # сохраняет только те поля что были изменены
        repr = dict()
        for name, field_obj in self.__dataclass_fields__.items():
            is_not_default_value = (value := getattr(self, name, (default := field_obj.default))) != default
            try:
                is_not_empty_factory = not (isinstance(value, field_obj.default_factory) and len(value) == 0)
            except TypeError:
                #default_factory is missing type  (<dataclasses._MISSING_TYPE object at ---)
                is_not_empty_factory = True
            if is_not_default_value and is_not_empty_factory:
                repr[name] = value #\ #list[list[str]] fixer
                    #if name not in self.parseable_fields else ['.'.join(i) for i in value]
        return repr

    def compute_sizes(self):
        total_len = 0
        repr = self.asdict__different()
        sizes = dict()
        for name, field_obj in self.__dataclass_fields__.items():
            if name not in repr:
                sizes[name] = None
                continue
            value = repr[name]
            str_value = str(value)
            item_len = len(str_value)
            sizes[name] = item_len
            total_len += item_len
        norm_sizes = {}
        for name, len_ in sizes.items():
            if len_ is None:
                norm_sizes[name] = None
            else :
                norm_sizes[name] = len_/total_len
        self._sizes_collector.append(norm_sizes)

    @property
    def filled_ratio(self):
        # сохраняет только те поля что были изменены
        fields_ = self.__dataclass_fields__
        total = len(fields_)
        if total == 0:
            return 0
        diff = self.asdict__different()
        not_default_or_empty = sum([total*fields_[key].size for key in diff.keys()])
        return not_default_or_empty / total

    def as_dict(self):
        return {
            'link': self.url__secondary_page
        }

    @classmethod
    def convert(cls, obj:any ):
        attrs_name = [i.name for i in fields(Element)]
        obj_as_dict = {name: getattr(obj, name, None) for name in attrs_name}
        return Element(**obj_as_dict)


    @classmethod
    def convert_group(cls, obj_group:list[any] ):
        """ Частный случай - поддержка прошлых версий"""
        obj_as_dict = {}
        for obj in obj_group:
            element_attrs_name = {i.name for i in fields(Element)}
            container_attrs_name = {i for i in dir(obj) if not i.startswith('_')}
            target_attrs_name = element_attrs_name.intersection(container_attrs_name)
            obj_as_dict.update({name: getattr(obj, name, None) for name in target_attrs_name })
        return Element(**obj_as_dict)
