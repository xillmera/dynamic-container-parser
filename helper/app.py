import pathlib
import pdb

from . import (
    Tk, ttk, IntVar,
    json,
    dataclass, asdict, field, fields,
    Item, Strategy,
    StrategyView, ConfigDirectoryChoseCombobox, StatusIndicator,
    ConfigurationManager, StrategyParserConfigurationManager,
    ConfigurationSelectChain, ScrollableSessionDataView,
    EntryDesc, Session, OperationStatus, ProgramConfig, showerror,
    Element, pprint, reload_strategy
)

class App(Tk):
    """
    Справка:

    Treeview
        <Double-1> - редактировать поле (не все возможны)
        <Shift-+> - добавить поле (выбрано должно быть раскрывающееся)
        <Shift-Delete> - удалить поле (выбрано должно быть из раскрывшегося) (из вложенных)
        <Shift-Up> - переместить поле (из вложенных) выше
        <Shift-Down> - переместить поле (из вложенных) ниже
    EntryPopup
        <Return> - сохранить поле
        <FocusOut> - отменить изменения
        <Control-a> - выделить весь текст
        <Escape> - отменить изменения

    """


    default_values = {}
    default_column_value = ''

    @property
    def default_column(self):
        return [self.default_column_value
                for i
                in self.columns]

    def get_column_id_by_name(self, name):
        return self.columns.index(name)

    def column_values_by_dict(self, input_dict) -> list:
        return [
            input_dict[name] if name in input_dict else self.default_column_value
            for name
            in self.columns
        ]

    @classmethod
    @property
    def __dep__raw_config(cls):
        p = pathlib.Path() / 'config.json'
        d = p.read_text(encoding='utf-8')
        j = json.loads(d)
        return j
    
    def __init__(self, global_config, program_config=None):
        if program_config is None:
            program_config = {}
        super().__init__()
        self.vars = {
            #'programm_config':ProgramConfig(**program_config),
            'strategy_frame':(frame:= ttk.LabelFrame(self, text='Strategy')),
            'status_frame': (status_frame := ttk.LabelFrame(self, text='Status', height=60)),
            'status_indicator': (ind := StatusIndicator(status_frame)),
            'subscroll_strategyView':(subscroll_frame:=ttk.Frame(frame)),
            'strategyView':(view:=StrategyView(subscroll_frame, raw_config=global_config['StrategyView'])),
            'strategyScroll':ttk.Scrollbar(subscroll_frame, command=view.yview),
            'strategy_buttons':{
                #'reset': ttk.Button(frame, text='reset', command=self.on_reset),
                #'extract': ttk.Button(frame, text='extract', command=self.on_export),
                #'clear': ttk.Button(frame, text='clear', command=self.on_clear),
                'test':ttk.Button(frame, text='validation', command=self.on_strategy_validation),
                'run':ttk.Button(frame, text='run (no backup)', command=self.on_strategy_run),
                'upd': ttk.Button(frame, text='backup', command=self.on_strategy_insertion),
                'save':ttk.Button(frame, text='cache value', command=self.on_strategy_cache),
                'copy':ttk.Button(frame, text='copy', command=self.on_strategy_copy),
                'paste':ttk.Button(frame, text='paste', command=self.on_strategy_paste),
                #correct formatting, incorrect (is_acceptable internal method)
            },
            'config_frame': ConfigurationManager(self,
                                                 status_upd_callback=ind.process_status,
                                                 strategy_export_callback= self.on_strategy_upd,
                                                 save_changes_callback=self.on_parser_save),
            'session_frame':(f_session:= ttk.LabelFrame(self, text='Session data')),
            'selection_chain':ConfigurationSelectChain(base_jsons=StrategyParserConfigurationManager._config_data),
            'session_data':ScrollableSessionDataView(f_session, visible_els=5),
            'session_internals': Session(),
            'debug_frame':(deb:= ttk.LabelFrame(self, text='Debug')),
            'test_buttons':{
                'configure':ttk.Button(deb, text='settings', command=self.on_settings),
                'pdb':ttk.Button(deb, text='pdb', command=self.on_pdb),
                'print':ttk.Button(deb, text='print_val', command=self.on_val_print),
                'save': ttk.Button(deb, text='save_parser', command=self.on_parser_save),
                'run_parser': ttk.Button(deb, text='run_parser', command=self.on_parser_run),
                'map_reload': ttk.Button(deb, text='reload_mapper', command=self.on_map_reload)
            }
        }
        self.vars['strategyView'].config(yscrollcommand=self.vars['strategyScroll'].set)
        self.vars['config_frame'].update_values(init_value=self.vars['selection_chain'])
        Strategy.set__is_test_configuration(True)

        button_box_px = 3
        ttk.Style().configure('remove.TButton', padx=1, pady=1, width=button_box_px, height=button_box_px, foreground='red', background='red')
        ttk.Style().configure('add.TButton', padx=1, pady=1, width=button_box_px, height=button_box_px, foreground='green', background='green')

        #self.test_insert()
        #self.bind('4', self.__backdoor)
        self.geometry('630x740+0+0')
        #self.geometry('800x600+832+107')
        self.title('ParserConfigurationHelper')
        #self.resizable(False, False)
        self.resizable(True, True)

    def on_map_reload(self, *_):
        reload_strategy()

    def on_strategy_copy(self, *_):
        sel_cont = self.vars['selection_chain']
        edit_strat = sel_cont.strategy_obj
        self.vars['session_internals'].copied_strategy = edit_strat

    def on_strategy_paste(self, *_):
        strat = self.vars['session_internals'].copied_strategy
        self.vars['strategyView'].insert_strategy(strat)

    def on_parser_run(self, *_) -> bool:
        prs = self.vars['selection_chain'].parser_obj
        Strategy.set__is_test_configuration(False)
        prs.configure_values(url=prs._element_extractor.test_url)
        for i in prs.parse():
            el = Element.fromextractor(i)
            el.compute_sizes()
            pprint(el.compute_unify_sizes())
            #pprint(el)
            #pprint(Element.convert(i).as_dict())
            break
        Strategy.set__is_test_configuration(True)

    def on_strategy_validation(self, *_) -> bool:
        future_strat = self.vars['strategyView'].extract_strategy()
        self.vars['strategyView'].insert_strategy(future_strat)
        is_ = Strategy.is_valid(future_strat)
        if is_:
            self.vars['status_indicator'].process_status(OperationStatus(
                flag='accepted',
                description='Strategy is valid'
            ))

        else :
            self.vars['status_indicator'].process_status(OperationStatus(
                flag='denied',
                description='Strategy isnt\'t valid'
            ))
        return is_

    def test_insert(self):
        l = self.vars['session_data'].view
        for i in range(20):
            l.append(EntryDesc(name='hello', value=i))

    def on_strategy_upd(self, conf: ConfigurationSelectChain, **kw):
        strat = conf.strategy_obj
        if conf.selected_strategy is None:
            self.vars['strategyView'].clear_widget()
        else :
            self.vars['strategyView'].insert_strategy(strat)

    def on_parser_save(self,*_):
        StrategyParserConfigurationManager.export_config_data_to_config_folder()

    def get_inserted_values(self) -> dict[str,any]:
        return {j.alias:j.value for j in [i.desc for i in self.vars['session_data'].view if i.is_chosen] if j.alias_is_acceptable}

    def on_val_print(self, *_):
        int = self.vars['session_internals']
        print(int.strategy_name, '>> ')
        pprint(int.executed_val)

    def on_strategy_run(self, *_):
        if not self.on_strategy_validation():
            return
        sel_cont = self.vars['selection_chain']
        cashed_strat, base_strat, extractor = sel_cont.cashed_strategy_obj, sel_cont.strategy_obj, sel_cont.extractor_obj
        future_strat = self.vars['strategyView'].extract_strategy()
        self.vars['strategyView'].insert_strategy(future_strat)
        cashed_strat.set_future_strat_request(future_strat)
        cashed_strat.set_error_request_true()
        cashed_strat.status_obj.set('Empty') #over cashed values
        #inserted_separated = self._inserted_values
        try:
            val = cashed_strat.exec(base_obj=extractor, priority_inserted=dict(self.get_inserted_values()))
            self.vars['session_internals'].executed_val = val
            self.vars['session_internals'].strategy_name = sel_cont.selected_strategy
            self.vars['status_indicator'].process_status(OperationStatus(
                flag='accepted',
                description='Strategy: no errors'
            ))
        except BaseException as err:
            err_text = str(err)
            self.vars['status_indicator'].process_status(OperationStatus(
                flag='denied',
                description='Strategy: '+err_text
            ))

    def on_strategy_insertion(self, *_):
        strat = self.vars['strategyView'].extract_strategy()
        chain = self.vars['selection_chain']
        chain.cashed_strategy_obj.strat = strat
        chain.strategy_obj = strat
        self.vars['status_indicator'].process_status(OperationStatus(
            description='Chain\'s strategy was updated'
        ))
        self.on_strategy_upd(chain)

    def on_strategy_cache(self, *_):
        session = self.vars['session_internals']
        val = session.executed_val
        name = session.strategy_name
        if val is not None:
            e = EntryDesc(name=name, value=val, alias=name)
            self.vars['session_data'].view.append(e)
            self.vars['status_indicator'].process_status(OperationStatus(
                flag='accepted',
                description='Session value sucсessfully accepted'
            ))
        else:
            self.vars['status_indicator'].process_status(OperationStatus(
                flag='denied',
                description='Session value is empty'
            ))

    def on_clear(self, *_):
        self.vars['strategyView'].clear_widget()

    def on_reset(self, *_):
        self.vars['strategyView'].reset_strategy()

    def on_insert(self, *_):
        pass

    def on_export(self, *_):
        strat = self.vars['strategyView'].extract_strategy()
        print(strat)

    def on_pdb(self, *_):
        pdb.set_trace()


    def on_settings(self, *_):
        pass

    def place(self):
        pack_base = {'expand': True, 'fill': 'both'}
        pack_frame = dict(fill='x')

        self.vars['config_frame'].pack(**pack_frame)
        self.vars['config_frame'].place_internals()
        self.vars['strategy_frame'].pack(**pack_base)
        self.vars['subscroll_strategyView'].pack(**pack_base)
        #self.vars['subscroll_strategyView'].pack_propagate(False)

        self.vars['strategyView'].pack(**pack_base, side='left')
        self.vars['strategyScroll'].pack(expand=True, fill='y')

        for num, bttn in enumerate(self.vars['strategy_buttons'].values()):
            pack_opt = {'expand': True, 'fill': 'x', 'side':'left'}
            bttn.pack(**pack_opt)

        self.vars['session_frame'].pack(**pack_base)
        self.vars['session_data'].pack(**pack_base)
        #self.vars['session_frame'].pack_propagate(False)
        self.vars['status_frame'].pack(**pack_base)
        self.vars['status_indicator'].pack(**pack_base)

        self.vars['debug_frame'].pack(**pack_frame)

        for num, bttn in enumerate(self.vars['test_buttons'].values()):
            pack_opt = {'side':'left'}
            bttn.pack(**pack_opt)

    
