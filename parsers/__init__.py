from ..utils import (
    Tag, Iterable, fields,
    ABCMeta, abstractmethod,
    ConfigField, AutoConfig__Mark,
    StrategyFailure, StrategyNotDetected,
    Element, FieldNotAvailable
)
#import pdb

"""
Note: чтобы работал механизм автоподбора 
из внешнего слоя (самой программы) 
нужно инициализировать используемые подмодули:
import parsers
from parsers import <parser-name>
"""

def errorless(func):
    '''
    Любые ошибки в логике приводят к
    - унификации ошибки
    - возврату None
    '''
    def test(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            return None
    return test

def converter__time(func):
    def proxy(*args, **kwargs):
        res = func(*args, **kwargs)
        res = res.replace('min','')
        hours, mins = 0, res
        if 'hr' in res :
            hours, mins = res.splite('hr')
        hours, mins = int(hours), int(mins)
        '''
                if not only_total_m:
            res = {
                'hours':hours,
                'minutes':mins,
                'total_minutes':hours*60+mins
            }
        else :
            res = hours*60+mins
        '''
        return hours*60+mins
    return proxy

# deprecated
# -----------------------------------------
# current

class AbstractParser(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def configure_values(self, url: str = '', js_render: bool = False):
        pass

    @abstractmethod
    def is_url_acceptable(self) -> bool:
        pass

    @abstractmethod
    def is_content_acceptable(self) -> bool:
        pass

    @abstractmethod
    def parse(self,
              st_el: int = None,
              ed_el: int = None,
              test_run: bool = False) -> Iterable['RecipyFieldsExtractor'] | StrategyFailure:
        pass


class UseableParser__Mark(AbstractParser):
    pass


class ConfigDependantParser(AbstractParser, AutoConfig__Mark):
    _alias = None #переопределить если название в URL отличается от полного
    custom_engine = None #переопределить
    CONTENT_FULLNESS_RATIO_BORDER: float = ConfigField(predefined_value=0.6)

    def _create_main_container(self): #debug
        return getattr(self, 'first_container')()

    def _create_data_container(self): #debug
        return getattr(self, 'second_container')()

    def __init__(self, url: str = '', js_render: bool = False):
        self.__name__ = self.__class__.__name__
        if self._alias is None:
            self._alias = self.__name__

        self._element_extractor = self._create_main_container()
        pass

    def configure_values(self, url: str = '', js_render: bool = False):
        config_items = {
            'url':url,
            'js_render':js_render
        }
        for name, value in config_items.items():
            assert self._element_extractor.is_attr_cashedstrategy(name)
            cashstrat = self._element_extractor.get_base_attr(name)
            cashstrat.set_attr('is_value', True)
            cashstrat.set_attr('default', value)

    def is_url_acceptable(self) -> bool:
        test_url = self._element_extractor.url.lower()
        return all([
            i.lower() in test_url
            for i in self._element_extractor.repr_url_parts
        ])

    def is_content_acceptable(self) -> bool:
        try:
            mi = self.parse(test_run=True)
            m = next(mi) #Extractor
            el = Element.convert(m)
            filled_ratio = el.filled_ratio
            print(f"{self._alias} >> {round(filled_ratio*100, 1)}% fields extracted")
            return filled_ratio > self.CONTENT_FULLNESS_RATIO_BORDER
        except (BaseException, StrategyFailure):
            return False

    def _data_iteration(self) -> list[Tag]:
        # подмена gr_content возможна
        res = self._element_extractor.elements
        return res


    def parse(self,
              st_el: int = None,
              ed_el: int = None,
              test_run: bool = False) -> Iterable['RecipyFieldsExtractor'] | StrategyFailure:

        error_stage = 'iteration'
        for num, gr_el_content in enumerate(self._data_iteration()):
            if st_el is not None and num < st_el:
                continue
            if ed_el is not None and ed_el < num:
                continue

            extractor_obj = self._create_data_container()

            extractor_obj.group_content = gr_el_content
            self._element_extractor.target_url = (sec_page_url := extractor_obj.url__secondary_page)
            extractor_obj.target_content = self._element_extractor.target_content
            print('state:', num, '—', sec_page_url)
            yield extractor_obj

            if test_run:
                break
        try:
            pass
        except BaseException as ex:
            raise StrategyFailure(f'Extraction problem. Mostly due wrong strategy configuration. {error_stage}')


def get_parse_strategy(url: str, js_render: bool, test_request:bool = False) -> tuple[AbstractParser] | StrategyNotDetected:
    for child in UseableParser__Mark.__subclasses__():
        child_obj = child()
        ch_name = child.__name__
        child_obj.configure_values(url=url, js_render=js_render)
        if child_obj.is_url_acceptable():
            if test_request:
                if not child_obj.is_content_acceptable():
                    print(ch_name, '(parser) content isn\'t acceptable', sep=' > ')
                    continue

            print(ch_name, '(parser) acceptable', sep=' > ')
            yield child_obj
        else :
            print(ch_name, '(parser) url isn\'t acceptable', sep=' > ')
    else:
        raise StrategyNotDetected


