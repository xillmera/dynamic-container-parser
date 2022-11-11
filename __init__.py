import pydantic, json

from .utils import (
    AutoConfig, InputArgs,
    StrategyFailure, StrategyNotDetected
)
from .parsers import (
    get_parse_strategy
)
from .utils import *
from .serialization import DbInteraction, FileInteraction

AutoConfig.get_initials_from()
AutoConfig.deliver_initials()
AutoConfig.update_config()
StrategyParserConfigurationManager.extract_config_data_from_config_folder()
pass

def url_processing(input_args: InputArgs):
    try:
        for strat in get_parse_strategy(input_args.url, input_args.js_render, input_args.additional_test_request):
            # obj because «is_content_acceptable» method leads to data caсhing
            try:
                for extractor in strat.parse(input_args.st_el, input_args.ed_el):
                    element = Element.convert(extractor)
                    try:
                        FileInteraction.save(element)
                    except:
                        continue
                    """
                    if input_args.db_save:
                        DbInteraction.save(extractor)
                    if input_args.json_save:
                        FileInteraction.save(extractor)
                    
                    """
                    #print('hello')
                break
            except StrategyFailure:
                continue

    except StrategyNotDetected:
        pass
