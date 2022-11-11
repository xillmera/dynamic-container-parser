from . import (
    dataclass, field, Strategy, CashedStrategy,
ExtractorsKeepable, StrategiesKeepable
)


@dataclass(init=True)
class ProgramConfig:
    auto_validation_after_edit: bool = False
    auto_backup_after_edit: bool = False
    auto_run_due_cache_value: bool = False
    over_cash_on_run :bool = True
    print_value_after_run: bool = True

@dataclass(init=True)
class Item:
    parent: str = ''
    index: int = 'end'
    iid: str = None
    text: str = ''
    values: tuple = ''
    tags: tuple = ''
    open: bool = False
    image: str = ''



@dataclass(init=True)
class OperationStatus:
    description: str = ''
    flag: str = 'neutral' #'accepted' | 'neutral' | 'denied'

    @property
    def color_by_state(self):
        match self.flag:
            case 'neutral':
                return ''
            case 'accepted':
                return 'green'
            case 'denied':
                return 'red'

@dataclass(init=True)
class ConfigurationSelectChain:
    base_jsons: dict = None
    selected_parser: str = None
    parser_obj: [object | ExtractorsKeepable] = None
    selected_extractor: str = None
    extractor_obj: [object | StrategiesKeepable] = None
    selected_strategy: str = None
    cashed_strategy_obj: CashedStrategy = None
    strategy_obj: Strategy = None


@dataclass(init=True)
class EntryDesc:
    is_include: bool = False
    name: str = ''
    value: any = None
    alias: str = None

    @property
    def alias_is_acceptable(self):
        return self.alias != ''


@dataclass(init=True)
class Session:
    strategy_name: str = ''
    executed_val: any = None
    copied_strategy: Strategy = None




