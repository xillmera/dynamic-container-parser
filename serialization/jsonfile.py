from . import Element, json, pathlib, AutoConfig__Mark, ConfigField


def create_full_dir_path(path: pathlib.Path):
    if path.exists():
        return
    not_exists = [pt_ for pt_ in [path, *path.parents] if not pt_.exists()]
    not_exists.reverse()
    [pt_.mkdir() for pt_ in not_exists]


class JSONSerialisation(AutoConfig__Mark):
    @staticmethod
    def _prepath_process(value:str):
        value = pathlib.Path(value)
        create_full_dir_path(value)
        return value

    prepath = ConfigField(after_process_callback=_prepath_process ,predefined_value='production/json')
    typical_name = ConfigField(predefined_value='recipy')

    class Scheme:
        def __init__(self, extractor: Element):
            self._ex = extractor

        def __str__(self):
            return json.dumps(self._ex.as_dict(),indent='\t')

    @classmethod
    @property
    def counter(cls):
        try:
            pth = cls.prepath / f"{cls.typical_name}_{cls._counter}.json"
            if pth.exists():
                cls._counter += 1
                return cls.counter
            else :
                return cls._counter
        except AttributeError:
            cls._counter = 0
            return cls.counter

    @classmethod
    @property
    def filepath(cls) -> pathlib.Path:
        return cls.prepath / f"{cls.typical_name}_{cls.counter}.json"

    @classmethod
    def serialize(cls, extractor: Element):
        cls.filepath.write_text(
            str(cls.Scheme(extractor)),
            encoding='utf-8'
        )