from . import (
    json, pathlib,
    Strategy,  StrategyFailure,
    AutoConfig__Mark, ConfigField,
    ConfigDependantParser, UseableParser__Mark,
    StrategiesKeepable, ExtractorsKeepable, EmptyContainerCreatable,
    StrategyMap, MapKeepable
)


class StrategyParserConfigurationManager(AutoConfig__Mark):
    class TemplParser:
        class TemplExtractor(AutoConfig__Mark):
            ERRORLESS_CONTAINER = ConfigField(predefined_value=True)

            class CashedStrategy(EmptyContainerCreatable):
                element_type = Strategy

                class Status:
                    class Value:
                        pass

                    Empty = Value()
                    Dynamic = Value()
                    Cashed = Value()
                    GenReady = Value()
                    GenInProgress = Value()
                    GenStopped = Value()

                    @property
                    def _possible(self):
                        return {
                            i: cont
                            for i
                            in dir(self)
                            if not i.startswith('_') and isinstance((cont := getattr(self, i)), self.Value)
                        }

                    def set(self, value: str):
                        assert value in self._possible, f'Manual err. No such ({value}) Status'
                        self._val = self._possible[value]

                    def __init__(self):
                        self._val = self.Empty

                    def __eq__(self, other: Value):
                        return id(self._val) == id(other)

                    def __repr__(self):
                        for name, val in self._possible.items():
                            if id(val) == id(self._val):
                                return name

                def __init__(self,
                             strat_obj= None,
                             is_errorless=True,
                             default_value=None):
                    self._strat = strat_obj if strat_obj is not None else Strategy()
                    self.is_cashing = strat_obj.is_cashed
                    self.is_gen = strat_obj.is_gen
                    self._is_errorless = is_errorless
                    self._default = default_value
                    self._cashed = None
                    self._gen = None
                    self.force_update = False
                    self._error_request = False
                    self._future_strat = None
                    self.status_obj = self.Status()

                @classmethod
                def create_empty(cls):
                    return cls(strat_obj=Strategy())

                def duplicate(self):
                    return self.__class__(strat_obj=self._strat.duplicate())

                @property
                def strat(self):
                    if self._future_strat is not None:
                        future_strat = self._future_strat #closed in exec
                        self._future_strat = None
                        return future_strat
                    return self._strat

                @strat.setter
                def strat(self, value: Strategy):
                    self._strat = value

                def set_future_strat_request(self, future_strat=None):
                    self._future_strat = future_strat

                @property
                def is_errorless(self):
                    if self._error_request:
                        self._error_request = False
                        return False
                    return self._is_errorless

                def set_error_request_true(self):
                    self._error_request = True

                def current_el_trace(self):
                    s1 = {conf.target_attr for conf in self.strat.getattr_iter('events')}
                    s2 = {conf.base_attr for conf in self.strat.getattr_iter('initial')}
                    s1.update(s2)
                    return s1

                def _is_trace_unique(self, before_trace = None):
                    #не допустимо закикливание:
                    if before_trace is None:
                        return True
                    else :
                        return len(before_trace.intersection(self.current_el_trace())) == 0

                #dep
                def _event_init_union(self) -> dict[str:dict]:
                    """
                    Обрабатывает строку events и initial
                    events: <field_name>.<status>, [...]
                    initials: <field_name>.<alias>, [...]
                    т.е третий параметр <status>
                    <field_name>.<alias>.<status>, [...]
                    он может отсутствовать
                    если отсутствует <alias> ставиться пустая строка
                    <field_name>..<status>

                    Обновляются все параметры, однако
                    в конечные данные попадают только с <alias> не ''(пустая строка)
                    """
                    events = {i[0]:{'alias':None,'status':i[1]} for i in self.strat.events}
                    initials = {i[0]:{'alias':i[1], 'status':None} for i in self.strat.initial}
                    union = dict({**events, **initials})
                    events_set = set(events)
                    initials_set = set(initials)
                    for key in initials_set.intersection(events_set):
                        union[key].update(events[key])
                    return union

                def exec(self, base_obj, before_trace: set = None, priority_inserted: dict[str:any] =None):
                    """
                    priority_inserted : dict( <alias>: <value> )
                    """
                    strat = self.strat #future strat policy implementation (one call)
                    
                    if strat.is_value:
                        return strat.default

                    assert self._is_trace_unique(before_trace=before_trace), 'Manual. Strategy Configuration. Recursion may occured during initialisation'
                    if any([
                        self.status_obj == self.Status.GenStopped,
                        self.status_obj == self.Status.Dynamic
                    ]):
                        self.status_obj.set('Empty')

                    for event_conf in strat.getattr_iter('events'):
                        ch_strat_obj = base_obj.get_base_attr(event_conf.target_attr)
                        assert isinstance(ch_strat_obj, self.__class__), f'Manual. Strategy Configuration. <{event_conf.name}> isn\'t CashedStrategy obj '
                        ch_strat_obj.status_obj.set(event_conf.name) #не обязательно запускать

                    initials = {}
                    if priority_inserted is not None:
                        initials = priority_inserted
                    for alias_conf in strat.getattr_iter('initial'):
                        if alias_conf.alias in initials:
                            continue
                        cur_trace = self.current_el_trace()
                        base_obj.set_before_trace(cur_trace)
                        _item = getattr(base_obj, alias_conf.base_attr)
                        value = _item.exec(priority_inserted=priority_inserted) \
                            if isinstance((_item), self.__class__) else _item
                        initials[alias_conf.alias] = value

                    result_val = None
                    if self.status_obj == self.Status.Empty:
                        try:
                            result_val = base_obj.map.execute(
                                init_values=initials,
                                info=strat
                            )
                            self.status_obj.set('Dynamic')
                            if self.is_cashing:
                                self._cashed = result_val
                                self.status_obj.set('Cashed')
                            if self.is_gen:
                                self._gen = iter(result_val)
                                self.status_obj.set('GenInProgress')
                        except BaseException as ex:
                            if self.is_errorless:
                                return self._default
                            else:
                                raise StrategyFailure(*ex.args)

                    if self.status_obj == self.Status.GenInProgress:
                        try:
                            self._cashed = next(self._gen)
                            self.status_obj.set('GenReady')
                        except StopIteration:
                            self.status_obj.set('GenClose')

                    self.set_future_strat_request()  # future strat request closure

                    if any([
                        self.status_obj == self.Status.Cashed,
                        self.status_obj == self.Status.GenReady
                    ]):
                        return self._cashed
                    if self.status_obj == self.Status.Dynamic:
                        return result_val

                def set_attr(self, name, value):
                    setattr(self.strat, name, value)

                def zip(self) -> dict[str:dict]:
                    # is_acceptable (check mro)
                    return self._strat.asdict()

            class StrategegyAsProperty__Mixin(AutoConfig__Mark):
                CASHED_STRATEGY_OBJ_VISIBILITY_IN_PDB = ConfigField(predefined_value=False)
                def __init__(self, *args, **kwargs):
                    super().__init__( *args, **kwargs)
                    self._is_next_attr_base = False
                    self._before_trace = None

                def next_attr_is_base(self):
                    self._is_next_attr_base = True

                def set_before_trace(self, trace: set):
                    self._before_trace = trace

                def get_strategy_from_base_attr(self, name):
                    return self.get_base_attr(name).strat

                get_strat = get_strategy_from_base_attr

                def get_base_attr(self, name):
                    return super().__getattribute__(name)

                def is_attr_cashedstrategy(self, name):
                    val = super().__getattribute__(name)
                    return isinstance(
                        val,
                        StrategyParserConfigurationManager.TemplParser. \
                            TemplExtractor.CashedStrategy
                    )

                def __getattribute__(self, name):
                    val = super().__getattribute__(name)
                    is_ = isinstance(
                        val,
                        StrategyParserConfigurationManager.TemplParser.\
                        TemplExtractor.CashedStrategy
                    )
                    debug_ = super().__getattribute__('CASHED_STRATEGY_OBJ_VISIBILITY_IN_PDB')
                    _before_trace = super().__getattribute__('_before_trace')
                    is_next_attr_base_ = super().__getattribute__('_is_next_attr_base')
                    #print(name, is_, is_next_attr_base_)
                    if is_ and not (debug_ or is_next_attr_base_):
                        val = val.exec(base_obj=self, before_trace=_before_trace)

                    if not name == 'next_attr_is_base':
                        self._is_next_attr_base = False
                    if not name == 'set_before_trace':
                        self._before_trace = None
                    return val

            @classmethod
            def _create_template(cls, name, cls_attrs):
                return type(
                    name,
                    (
                        cls.StrategegyAsProperty__Mixin,
                        StrategiesKeepable,
                        EmptyContainerCreatable,
                        MapKeepable,
                        object
                    ),
                    cls_attrs
                )

            @staticmethod
            def _convert_config_extractor_json_part_into_strategies(input_: dict[dict]) -> dict[str:Strategy]:
                return {
                    strategy_name: Strategy.fromdict(strategy_payload)
                    for strategy_name, strategy_payload
                    in input_.items()
                }


            @classmethod
            def _convert_strategy_into_attribute(cls, strat):
                return cls.CashedStrategy(
                    strat_obj=strat,
                    is_errorless=cls.ERRORLESS_CONTAINER,
                    default_value=strat.default
                )

            @classmethod
            def create_empty(cls, name='Extractor'):
                return cls.create(name, {})

            @classmethod
            def create(cls, name, extractor_data) -> type:
                strategies = cls._convert_config_extractor_json_part_into_strategies(input_=extractor_data)
                attributes = {
                    'map': StrategyMap,
                    '__strategies__':list(strategies.keys()),
                    'element_type':cls.CashedStrategy,
                    'create_empty':cls.create_empty
                }
                cls_template = cls._create_template(name=name, cls_attrs=attributes)
                for attr_name, strat in strategies.items():
                    attr = cls._convert_strategy_into_attribute(strat=strat)
                    setattr(cls_template, attr_name, attr)
                return cls_template

            @classmethod
            def zip(cls, class_: StrategiesKeepable) -> dict[str:dict]:
                # is_acceptable (check mro)
                repr = dict()
                for strat_name in class_.__strategies__:
                    strat : [cls.CashedStrategy, object] = getattr(class_, strat_name)
                    strat_json = strat.zip()
                    repr[strat_name] = strat_json
                return repr

        @staticmethod
        def _create_template(name, cls_args, is_template_parser:bool = False):
            _mro = [object]
            _mro.insert(0, UseableParser__Mark)
            _mro.insert(0, ExtractorsKeepable)
            if is_template_parser:
                _mro.insert(0, ConfigDependantParser)
            return type(
                name,
                tuple(_mro),
                cls_args
            )

        @classmethod
        def create(cls, config_data: dict, name: str):
            #Либо класс полностью кастомный, либо на заготовках (не обрабатывается)
            extractors = {
                name: cls.TemplExtractor.create(name=name,
                                                extractor_data=extractor_data)
                for name, extractor_data
                in config_data.items()
                if isinstance(extractor_data, dict)
            }
            is_template_parser = config_data.get('is_template_parser', False)
            attributes = {
                **extractors,
                '__extractors__':list(extractors.keys()),
                '__settings__':{
                    'is_template_parser':is_template_parser
                }
            }
            return cls._create_template(name=name,
                                        cls_args=attributes,
                                        is_template_parser=is_template_parser)

        @classmethod
        def zip(cls, class_: ExtractorsKeepable) -> dict[str:dict]:
            # is_acceptable (check mro)
            repr = dict()
            for extr_name in class_.__extractors__:
                extr = getattr(class_, extr_name)
                extr_json = cls.TemplExtractor.zip(class_=extr)
                repr[extr_name] = extr_json
            for name, value in class_.__settings__.items():
                repr[name] = value
            return repr

    @classmethod
    def _extract_extractor_n_strategies(cls, source_jsons: dict[str:dict]):
        """ typical config sturcture:
            /bbcgoodfood.json
            {
                "RecipyElementsExtractor":{
                    elements:{
                        #strategy
                    }
                }
                "RecipyDataExtractor":{
                    #strategies
                }
            }
        #afterprocess_callback
        """
        cls._config_data = {
            name: cls.TemplParser.create(
                config_data = data,
                name = name
            )
            for name, data
            in source_jsons.items()
        }

    @staticmethod
    def _get_base_config_folder() -> str:
        return str((pathlib.Path(__file__).parent / r'..\..\parsers\configs').absolute())

    CONFIG_FOLDER: pathlib.Path = ConfigField(
        after_process_callback=lambda x: pathlib.Path(x) ,
        predefined_value=_get_base_config_folder()
    )
    _config_data: dict = None
    ERRORLESS_CONTAINER: bool = ConfigField(predefined_value=True)

    @classmethod
    def extract_config_data_from_config_folder(cls) -> dict[dict]:
        #хранит созданные классы чтобы можно было использовать интерфейс <UseableParser__Mark>
        cls._extract_extractor_n_strategies(source_jsons={
            item.stem: json.loads(
                    item.read_text(
                        encoding='utf-8'))
            for item
            in cls.CONFIG_FOLDER.iterdir()
            if item.suffix == '.json'
        })

    @classmethod
    def export_config_data_to_config_folder(cls) -> dict[dict]:
        for parser_name, parser_class in cls._config_data.items():
            json_cont = cls.TemplParser.zip(class_=parser_class)
            f_name = f'{parser_name}.json'
            f = cls.CONFIG_FOLDER / f_name
            j_repr = json.dumps(json_cont, indent='\t')
            f.write_text(j_repr, encoding='utf-8')


