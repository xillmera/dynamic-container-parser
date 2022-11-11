from . import (
    ABCMeta, abstractproperty,
    json, requests,
    BeautifulSoup, Tag,
    Strategy,
    StrategyFailure,
    AutoConfig__Mark, ConfigField,
)


class StrategyMap(AutoConfig__Mark):
    class Engine__Mark(metaclass=ABCMeta):
        alias = abstractproperty()

    class HtmlReceiver(AutoConfig__Mark, Engine__Mark):
        alias = 'hrecv'
        HEADERS = ConfigField(predefined_value={
            'User-Agent': r'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            #'Accept-Encoding': "gzip, deflate, br" #(контент меньше весит но нужен метод декодирования. Опять же не все сервера отдают закодированный контент.) (справка - алгоритмы сжатия https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept-Encoding)
        })
        SPLASH_SERVER_RENDER_PAGE: str = ConfigField()
        SPLASH_RENDER_WAIT = ConfigField(predefined_value=10)

        @classmethod
        def convert_output(self, output, encode_mode='bs', **kwargs) -> Tag | str | None:
            req: requests.models.Response = output
            if req.status_code != 200:
                raise StrategyFailure(f'Web Request ended with failure status code ({req.status_code})')
            html = req.text.replace('\t', '').replace('\n', '') #auto unescaping (breaks json)
            match encode_mode:
                case 'raw':
                    return html
                case _:
                    return BeautifulSoup(html, 'html.parser')


        @classmethod
        def basic(cls, url, **kwargs):
            return requests.get(url, headers=cls.HEADERS)

        @classmethod
        def javascript_rendered(cls, url, **kwargs):
            return requests.get(cls.SPLASH_SERVER_RENDER_PAGE,
                                params={'url': url, 'wait': cls.SPLASH_RENDER_WAIT})

        @classmethod
        def unify(cls, url, js_render=None, **kwargs):
            if js_render is None or not js_render:
                return cls.basic(url)
            else :
                try:
                    return cls.javascript_rendered(url)
                except:
                    raise StrategyFailure('Javascript render engine not configured')

    class Receiver(Engine__Mark):
        alias = 'recv'

        @classmethod
        def one(cls, soup, sel, **kwargs) -> Tag | None:
            return soup.select_one(sel)

        @classmethod
        def multi(cls, soup, sel, **kwargs) -> list[Tag] | None:
            return soup.select(sel)

        @classmethod
        def one_chain(cls, soup, sel_chain: list[str], **kwargs) -> Tag | None:
            target_tag = soup
            for sel in sel_chain:
                target_tag = cls.one(target_tag, sel)
                if target_tag is None:
                    break
            return target_tag

        @classmethod
        def multi_chain(cls, soup_list: list[Tag], sel_chain: list[str], **kwargs) -> list[Tag] | None:
            return [cls.one_chain(soup, sel_chain) for soup in soup_list]

    class Processor(Engine__Mark):
        alias = 'proc'

        @classmethod
        def restore_url(cls, url: str, **kwargs) -> str:
            if url.startswith('//'):
                url = f'https:{url}'
            return url

        @classmethod
        def text_oneline(cls, soup, **kwargs) -> str:
            return getattr(soup, 'text', None)

        @classmethod
        def text_multiline(cls, soup_list: list[Tag], **kwargs) -> str:
            return '\n'.join([i.text for i in soup_list])

        @classmethod
        def string_delimiter(cls, soup: Tag, **kwargs):
            #for ellements separated by `<!-- -->` operator
            return [i.replace(',', '').strip() for i in soup.strings]

        @classmethod
        def href_url(cls, soup, **kwargs) -> str:
            return soup.get('href')

        @classmethod
        def src_url(cls, soup, **kwargs) -> str:
            return soup.get('src')

        @classmethod
        def src_url_no_post(cls, soup, **kwargs) -> str:
            return cls.src_url(soup).split('?')[0]

        @classmethod
        def contains(cls, soup, sequence:str, **kwargs) -> bool:
            print(soup.text.lower(), sequence.lower(), sequence.lower() in soup.text.lower())
            return sequence.lower() in soup.text.lower()

        @classmethod
        def get_marked(cls, item_list:list[any], proxy_marks:list[bool], **kwargs):
            if len(item_list) != len(proxy_marks):
                raise StrategyFailure('Wrong proxy_marks list size')
            for i, flag in zip(item_list, proxy_marks):
                if flag:
                    return i
            else :
                raise StrategyFailure('No true mark for any item')



        @classmethod
        def servings_strip(cls, prep_str, **kwargs) -> Tag:
            return prep_str.replace('Serves ', '').strip()
        
        @classmethod
        def no(cls, item, **kwargs) -> Tag:
            return item

        @classmethod
        def zip(cls, item_1: list, item_2: list, **kwargs) -> list[tuple]:
            return list(zip(item_1,item_2))

        @classmethod
        def multi_zip(cls, **kwargs) -> list[tuple]:
            m= list(zip( *[
                kwargs[i]
                for i
                in kwargs
                if 'zip' in i and isinstance(kwargs[i], list)
            ] ))
            #pprint(m)
            return m


        @classmethod
        def __fields__(cls):
            return [i for i in dir(cls) if not i.startswith('_')]

    class ConverTime(Engine__Mark):
        alias = 'tm'
        """
        Возвращает количество минут.
        могут различаться входные данные
        """

        @classmethod
        def get_by_tag(cls, soup_list: list[Tag], tag: str, **kwargs):
            for soup in soup_list:
                if tag.lower() in soup.text.lower():
                    return soup
            else:
                raise StrategyFailure('No such time field')

        @classmethod
        def get(cls, soup, **kwargs) -> str:
            return soup.get('datetime')

        @staticmethod
        def html_type(time: str, **kwargs) -> int:
            tmp = time.removeprefix('PT')
            h, m = tmp.split('H')
            h = int(h)
            m = int(m.removesuffix('M'))
            return h * 60 + m

        @staticmethod
        def base(time: str, **kwargs) -> int:
            time = time.replace('min', '')
            hours, mins = 0, time
            if 'hr' in time:
                hours, mins = time.split('hr')
            hours, mins = int(hours), int(mins)
            return hours * 60 + mins

    class StringEditor(Engine__Mark):
        alias = 'sedit'

        @classmethod
        def add_to_st(cls, base, additive, **kw):
            return f'{additive}{base}'


    class Util(Engine__Mark):
        alias = 'util'

        @classmethod
        def index(cls, cont, idx, **kwargs):
            if isinstance(idx, str):
                idx = int(idx)
            return cont[idx]

        @classmethod
        def get_item(cls, element, item, **kwargs):
            return element[item]

        @classmethod
        def asjson(cls, cont, **kwargs):
            return json.loads(cont)

        @classmethod
        def enumerate(cls, item_list, **kwargs) -> list[tuple[int,any]]:
            return [(num, item) for num, item in enumerate(item_list)]

        @classmethod
        def url_page_swap(cls, url, counter: int, miss_counter: int = 0, **kwargs) -> str:
            new_url = url if miss_counter == counter else f'{url}?page={counter}'
            counter += 1
            return new_url

        @classmethod
        def one_url(cls, url, flag: bool, **kwargs) -> str:
            if not flag:
                flag = not flag
                return url
            raise StrategyFailure('Next url iteration not provided')

        @classmethod
        def url_filling(cls, part_url: str, base_url: str, **kwargs) -> str:
            return f'{base_url}{part_url}' if part_url[0] == '/' else part_url


        @classmethod
        def receive_attr(cls, element, attr, **kwargs):
            return getattr(element, attr)

        @classmethod
        def get(cls, element, attr, **kwargs):
            return element.get(attr)

    class CustomEngine(Engine__Mark):
        alias = 'spec'


    SEQUENCE_ELEMENT_SEPARATOR: str = ConfigField(predefined_value=',')

    @classmethod
    def execute(self,
                 init_values: dict[any],
                 info: Strategy):#, cls: type = None):
        f"""
        Запускает последовательную обработку данных с помощью "Стратегий"
        по очередности указания в строке "strategies_config_sequence"

        Строка имеет следующий вид:
        "<internal_engine_class_name>.<engine_submethod_name>[!<foreach_subkey>!<target_subkey>][@<base_item>@<proxy_item>...].<output_param_name>"
        > internal_engine_class_name - на текущий момент {[i.alias for i in self.Engine__Mark.__subclasses__()]} 
            + 'cstm' | 'spec' (for user defined single processor)
        > engine_submethod_name - множество различных
            [дополнительные параметры] для стратегий итерации по множеству
            > foreach_subkey - ключ по которому будет итерирование
            > target_subkey - ключ в который размещается элемент итерирования
            [дополнительные параметры] (добавляются кратно 2) для переименования элементов
                в контексте между ступенями обработки
            > base_item - имя переменной в контексте которая переименовывается
            > proxy_item - новое имя для указанной переменной
        > output_param_name - отвечает за такой тег, который будет доступен
            на входе следующей стратегии / в который размещается результат работы 
            текущей стратегии 
        
        Execution rules :
            если return_key заполнен до завершения всех конфигураций - выходит из исполнения с тем что есть
        """

        temp_kwargs = dict(info.context)
        # {init-val-name: recieve-callback}

        temp_kwargs.update(**init_values)

        #print(info.config_sequence)
        last_key = None
        for ln_conf in info.getattr_iter('config_sequence'):
            if ln_conf.is_stop:
                break
            if ln_conf.is_test:
                continue
            last_key = ln_conf.return_subkey
            engine_class__ = None
            for engine_class_ in self.Engine__Mark.__subclasses__():
                if ln_conf.type_ == engine_class_.alias:
                    engine_class__ = engine_class_
                    break
            else:
                raise TypeError(f'Matching subclass {ln_conf.type_} not exist (manual err)')

            try:
                engine = getattr(engine_class__, ln_conf.name)
            except AttributeError:
                raise StrategyFailure(f'Such strategy name ({ln_conf.name}) not acceptable for engine ({engine_class__.__name__})')

            executable_args = temp_kwargs
            if ln_conf.proxy_items is not None:
                executable_args.update({
                    proxy_item:temp_kwargs[base_item]
                    for base_item, proxy_item
                    in ln_conf.proxy_items
                })
            if ln_conf.foreach_subkey is None:

                temp_kwargs[ln_conf.return_subkey] = engine(**executable_args)
            else :
                iterable_inst = temp_kwargs[ln_conf.foreach_subkey]
                if not isinstance(iterable_inst, list):
                    raise StrategyFailure(f'Instance ({type(iterable_inst)}) not iterable')

                temp_kwargs[ln_conf.return_subkey] = [
                    engine(**{**executable_args, ln_conf.target_subkey:i})
                    for i
                    in iterable_inst
                ]
            if temp_kwargs.get(info.return_key, None) is not None:
                break
        ret_key = info.return_key
        if ret_key not in temp_kwargs:
            return temp_kwargs[last_key]
        return temp_kwargs[ret_key]

    def __str__(self) -> dict:
        return {
            possible_class_.__name__: [
                possible_method_
                for possible_method_
                in possible_class_.__dict__.values()
                if getattr(possible_method_, '__text_signature__', False)
            ]
            for possible_class_
            in self.__dict__.values()
            if getattr(possible_class_, '__class__', False)
        }
