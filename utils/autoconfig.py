"""
AutoConfig__Mark - метка классов которым требуется конфигурирование
    внутренних значений (их доставка)
ConfigField - Идентификатор поля с указанием особенностей обработки
AutoConfig - менеджер через который осуществляется доставка
"""


from . import (
    json, JSONEncoder,
    pathlib,
    Iterable,
    AutoConfig__Mark,
    WrongConfiguration
)


class UsrJSONEncoder(JSONEncoder):
    def default(self, o: any) -> any:
        if isinstance(o, pathlib.Path):
            return str(o)
        return JSONEncoder.default(self, o)


class ConfigField:
    def __init__(self, after_process_callback= lambda x: x, predefined_value: any = None, dependant: bool = False):
        self._predefined_value = predefined_value
        self._process_method = after_process_callback
        self._dependant = dependant

    def is_dependant(self) -> bool:
        return self._dependant

    def _process(self, value):
        value = value if value is not None else self._predefined_value
        return self._process_method(value)


class AutoConfig:
    _config_data: dict = None
    _config_placement: pathlib.Path = None
    _amount__tries = 2

    @classmethod
    @property
    def _config_classes(cls) -> Iterable[type]:
        return AutoConfig__Mark.__subclasses__()

    @staticmethod
    def _get_base_config_file_placement():
        return pathlib.Path(__file__).parent / r'..\config.json'

    @classmethod
    def get_initials_from(cls, placement: pathlib.Path=None):
        """ Получает данные из конфиг-json
        если нет - создает пустое хранилище
        """
        if placement is None:
            placement = cls._get_base_config_file_placement()
        cls._config_placement = placement

        try:
            cls._config_data = json.loads(placement.read_text(encoding='utf-8'))
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            print('Broken cofig...')
            cls._config_data = {}

    @classmethod
    def deliver_initials(cls, *args, **kwargs):
        """ Проходит по всем классам унаследованным от AutoConfig__Mark
        Заменяет все классовые поля с типом ConfigField на:
        - predefined_value
        - полученное из get_initials_from
            - с доп. обработкой если таковая имеется (after_process_callback)
        """
        tmp_config_data = {}
        if cls._config_data is None:
            cls._config_data = {}
        all_config_residents_queue = []
        all_config_residents_queue_residue = []
        for subcls in cls._config_classes:
            all_config_residents_queue += [
                (key, value, subcls) for key, value
                in subcls.__dict__.items()
                if isinstance(value, ConfigField)
            ]

        try_cntr = 0
        while len(all_config_residents_queue) != 0:
            for num, (key, field_, subcls) in enumerate(all_config_residents_queue):
                pseudo_key = None \
                    if (tmp_config_data.get(key) is None and \
                        cls._config_data.get(key) is None) \
                    else tmp_config_data[key] if key in tmp_config_data else cls._config_data[key]
                if field_.is_dependant() and pseudo_key is None:
                    all_config_residents_queue_residue.append((key, field_, subcls))
                    continue
                if field_.is_dependant():
                    proc_val = pseudo_key
                else:
                    proc_val = field_._process(cls._config_data.get(key))

                params = (
                    subcls,
                    key,
                    proc_val
                )
                if not field_.is_dependant():
                    tmp_config_data[key]= proc_val

                setattr(*params)
            all_config_residents_queue, all_config_residents_queue_residue =\
                all_config_residents_queue_residue.copy(), []

            if try_cntr > cls._amount__tries:
                raise WrongConfiguration('Один из параметров autoconfig__mark задан неверно')
            try_cntr += 1

        cls._config_data = {
            key: cls._config_data[key]
            if key in cls._config_data
            else tmp_config_data[key]
            for key in tmp_config_data
        }

    @classmethod
    def update_config(cls):
        """Обновляет конфиг-json-файл
        """
        status = 'updated'
        if not cls._config_placement.exists():
            status = 'created'
        cls._config_placement.write_text(
            json.dumps(
                cls._config_data,
                indent='\t',
                cls=UsrJSONEncoder
            ),
            encoding='utf-8')
        print(f'Config was {status}...')