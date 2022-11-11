import pdb
import tkinter

from . import (
    ttk, asdict, StringVar, ABCMeta, abstractmethod, askdirectory,
    dataclass, Strategy, Item, fields, pathlib, threading, sleep,
    json, ConfigurationSelectChain, StrategyParserConfigurationManager,
    StrategiesKeepable, ExtractorsKeepable, tk, EntryDesc, Thread,
    CashedStrategy, OperationStatus, sqrt, showerror, askquestion
)


class SessionDataView(ttk.Frame, list):
    """
    simple list :
    - add at the end
    - clear_all

    columns: is_include, name, value, alias
    line: RadioButton + Label + EnterLabel + Entry
    subclass EnterLabel:
        on <Enter> create TopLevel Window with extended descripton
    !possible but not nessesery: save choises for each ConfigurationSelectionChain separately
    """

    def __init__(self,
                 *args,
                 resize_callback=lambda x: x,
                 scroll_upd_callback=lambda x: x,
                 visible_els=10,
                 **kwargs):
        # kwargs['background'] = 'white'
        #print(kwargs)
        list.__init__(self)
        ttk.Frame.__init__(self, *args, **kwargs)

        ttk.Style().configure('Small.TButton', background='red', width=2, height=2, padx=3, pady=3)
        ttk.Style().configure('Sep.TFrame', padx=1, pady=1)

        self.scroll_upd_callback = scroll_upd_callback
        self.resize_callback = resize_callback

        self._visible_els = visible_els
        self._visible_els_proxy = visible_els
        self.visible_st_idx = 0
        self.pseudo_scroll_element_cursor_line = 0.5 * 1 / visible_els

        self.bind('<MouseWheel>',self.on_mouse_wheel)
        self.bind('<Configure>', self.on_window_resize)

    @property
    def visible_els(self):
        if self._visible_els_proxy < self._visible_els:
            return self._visible_els_proxy
        return self._visible_els

    @visible_els.setter
    def visible_els(self, value):
        self._visible_els_proxy = value

    def on_mouse_wheel(self, event):
        #print(event)
        pass

    def on_window_resize(self, event):
        #print(event)
        new_height = event.height
        raw = new_height / self.Entry.typical_height
        self.visible_els = int(raw)

    class Entry(ttk.Frame):
        conf_label_width = 10
        cont_value_width = 20
        typical_height = 25

        class ExpandLabel(ttk.Label):
            conf_repr_len_sym_limit = 20

            class DelayFocusRecognizer(Thread):
                standart_sleep = 0.5

                def __init__(self, spawn_callback=lambda *_: None, delay=3):
                    super().__init__()
                    self.is_out = False
                    self.delay = delay
                    self.spawn_callback = spawn_callback

                def set_out(self):
                    self.is_out = True

                def reset(self):
                    self.is_out = False

                def run(self):
                    # ?? является ли join(timeout=0) завершающим поток событием??
                    # print('thr_start')
                    cntr = 0
                    spawn_req = False
                    while not self.is_out:
                        sleep(self.standart_sleep)
                        cntr += 1
                        if cntr > self.delay:
                            spawn_req = True
                            break
                    if spawn_req:
                        self.spawn_callback()
                    # print('thr_end')

            class TemporaryDescription(tk.Toplevel):
                symbol_line_limit = 32
                window_size_per_symbol_ratio = 240 / 32

                def _dep__compute_sizes(self):
                    """
                    #geometry_sizes = self.winfo_toplevel().winfo_geometry().split('+')[0]
                    #width, height = [int(i) for i in geometry_sizes.split('x')]
                    #width, height = 200, 200
                    #width = height = int(len(text)/3)
                    #scr_x, scr_y = self.winfo_screenwidth(), self.winfo_screenheight()
                    #if width > 400:
                    #    width=height=400
                    #print(x, y)
                    y -= 30
                    #print(scr_x, scr_y)
                    x_down, y_down = x+width, y+height

                    #print(x_down, y_down)
                    if x_down > scr_x:
                        x += scr_x - x_down
                    if y_down > scr_y:
                        y += scr_y - y_down
                    #print(x, y)
                    """
                    pass
                def __init__(self, *args, text='', spawn_pos=(0, 0), **kw):
                    super().__init__(*args, **kw)
                    # self.overrideredirect(True)
                    # self.wm_attributes('-toolwindow', True)
                    # Выглядит конечно хорошо, но мельком появляется исходная рамка
                    # и это раздражает восприятие
                    width = height = 300
                    self.symbol_line_limit = int(width / self.window_size_per_symbol_ratio)
                    self.wm_attributes('-topmost')
                    self.attributes('-alpha', 0.8)
                    x, y = spawn_pos
                    geo = '{}x{}+{}+{}'.format(width, height, x, y)
                    self.geometry(geo)
                    self.label = ttk.Label(self, text=self.convert_text_base(text))
                    # TODO добавить зависимость от количества строк
                    self.label.pack(expand=True, fill='both')
                    self.bind('<Leave>', lambda *_: self.destroy())

                @classmethod
                def convert_text_base(cls, text):
                    parts = []
                    idx = 0
                    while idx < len(text):
                        new_idx = idx + cls.symbol_line_limit-2
                        parts.append(text[idx:new_idx])
                        idx = new_idx
                    return '>\n<'.join(parts)

                @classmethod
                def convert_text_words(cls, text):
                    class SpecLineList(list):
                        def append(self, value: list[str]):
                            super().append(' '.join(value))

                        def __str__(self):
                            return '\n'.join(self)

                    parts = SpecLineList()
                    line = []
                    words = text.split(' ')
                    curr_len = 0
                    for word in words:
                        word_len = len(word) + 1  # пробел
                        curr_len += word_len
                        if curr_len > cls.symbol_line_limit:
                            parts.append(line)
                            curr_len = word_len
                            line = [word]
                        else:
                            line.append(word)
                    else:
                        parts.append(line)  # спрятанное преобразование list[str] -> space separate str
                    return str(parts)

            def __init__(self, *args, value, print_callback=lambda x: x, **kwargs):
                self.print_callback = print_callback
                self.value = value
                self.var = tk.StringVar(value=self.get_strip_repr())
                kwargs['textvariable'] = self.var
                super().__init__(*args, **kwargs)
                self.bind('<Enter>', self.on_enter)
                self.bind('<Leave>', self.on_out)

                self.potential_extended_description_window_manager: 'DelayFocusRecognizer' = None

            def on_enter(self, event):
                """
                TODO (исследовать) сделать распознавание единым для всех элементов
                    возможно понадобятся коллбэки через 2 уровня... (idx в частности)
                """
                # print('Enter:')
                if self.potential_extended_description_window_manager is not None and \
                        self.potential_extended_description_window_manager.is_alive():
                    self.potential_extended_description_window_manager.reset()
                    return
                self.potential_extended_description_window_manager = \
                    self.DelayFocusRecognizer(spawn_callback=self.on_spawn)
                self.potential_extended_description_window_manager.start()

                # self.print_callback(additional='enter')

            def on_out(self, event):
                # print('out (internal)')
                self.potential_extended_description_window_manager.set_out()
                # self.print_callback(additional='out')

            def on_spawn(self):
                spawn_pos = (self.winfo_rootx(), self.winfo_rooty())
                self.TemporaryDescription(self, text=str(self.value), spawn_pos=spawn_pos)

            def get_strip_repr(self):
                return str(self.value)[:self.conf_repr_len_sym_limit]

        def __init__(self, *args, id_, cont, remove_callback=lambda cur_id: cur_id, **kwargs):
            super().__init__(*args, **kwargs)
            self.base = cont
            self.id_ = tk.StringVar()
            self.id_label = ttk.Label(self, textvariable=self.id_)
            self.set_id(id_)
            self.is_include_var = tk.BooleanVar(value=cont.is_include)
            self.cb = ttk.Checkbutton(self, variable=self.is_include_var)
            self.name_l = ttk.Label(self, text=cont.name, width=self.conf_label_width)

            self.value_l = self.ExpandLabel(self, value=cont.value, print_callback=self.print_id,
                                            width=self.cont_value_width)
            self.alias_var = tk.StringVar(value=cont.alias)
            self.entry = ttk.Entry(self, textvariable=self.alias_var)
            self.remove_callback = remove_callback
            self.btr = ttk.Button(self, text='-', command=self.on_rem, style="Small.TButton")
            for i in [self.id_label, self.cb, self.name_l]:
                i.pack(side='left', fill='both')
            for i in [self.value_l, self.entry]:
                i.pack(expand=True, side='left', fill='both')
            self.btr.pack(side='left')

        @property
        def is_chosen(self):
            return self.is_include_var.get()

        def on_rem(self, *_):
            self.remove_callback(int(self.id_.get()) - 1)

        def print_id(self, additional=''):
            print(additional, self.id_.get())

        def set_id(self, id_):
            self.id_.set(str(id_ + 1))

        @property
        def desc(self):
            return EntryDesc(
                is_include=self.is_include_var.get(),
                name=self.base.name,
                value=self.base.value,
                alias=self.alias_var.get()
            )
    pack_options = dict(expand=True, fill='x')
    # proxy list part
    def append(self, value: EntryDesc):
        e = self.Entry(self, id_=len(self), cont=value, remove_callback=self.pop, style='Sep.TFrame')
        super().append(e)
        e.pack(self.pack_options)
        self.resize_callback(len(self))
        self._update_visible_els()

    def _update_visable_id_callback(self):
        for id_, entry_ in enumerate(self):
            entry_.set_id(id_)

    def pop(self, index=None):
        e = super().pop(index)
        e.destroy()
        self.resize_callback(len(self))
        self._update_visable_id_callback()
        self._update_visible_els()

    def get_chosen(self) -> list[EntryDesc]:
        for i in self:
            if i.is_chosen:
                yield i.desc

    def get_entry(self, idx) -> Entry:
        return list.__getitem__(self, idx)

    def __getitem__(self, idx) -> EntryDesc:
        e = self.get_entry(idx)
        return e.desc

    # inwidget appearence part
    @property
    def visible_end_idx(self):
        return self.visible_st_idx + self.visible_els - 1

    @property
    def visible_area_ratio(self) -> tuple[float, float]:
        total = len(self)
        st_val = 0.0
        end_val = 1.0
        if total > self.visible_els:
            end_val = 1.0 - (total - self.visible_end_idx) / total
            st_val = self.visible_st_idx / total
        st_val = st_val + self.pseudo_scroll_element_cursor_line
        end_val = end_val + self.pseudo_scroll_element_cursor_line
        return (st_val, end_val)

    def _update_scroll_widget(self):
        self.scroll_upd_callback(*self.visible_area_ratio)

    def set_yview(self, move_to_ratio):
        # move_to - scroll up pos + relative = absolute
        # print(move_to_ratio)
        base_pseudo_ratio = 0.5 * 1 / self.visible_els
        total = len(self)
        if total == 0:
            return
        max_ratio = (total - self.visible_els) / total + base_pseudo_ratio
        # print(move_to_ratio, max_ratio)
        if move_to_ratio < 0:
            #possible_st_el_pseudo_part = base_pseudo_ratio
            possible_st_el_pseudo_part = 0.0
            possible_st_el_idx = 0
        elif max_ratio < move_to_ratio:
            possible_st_el_idx = total - self.visible_els
            possible_st_el_pseudo_part = base_pseudo_ratio
        else:
            el_idx_raw = move_to_ratio * total
            el_idx_round = round(el_idx_raw)
            el_idx_pseudo = (el_idx_raw - el_idx_round) * 1 / self.visible_els
            possible_st_el_idx = el_idx_round
            possible_st_el_pseudo_part = el_idx_pseudo
        #print(possible_st_el_idx, possible_st_el_pseudo_part)
        self.visible_st_idx = possible_st_el_idx
        self.pseudo_scroll_element_cursor_line = possible_st_el_pseudo_part
        self._update_visible_els()

    def _update_visible_els(self):
        for el in self:
            el.pack_forget()
        for num, el in enumerate(self):
            if self.visible_st_idx <= num and num <= self.visible_end_idx:
                el.pack(self.pack_options)
        self._update_scroll_widget()

    def _dep_get_info(self, index=None):
        e = list.__getitem__(self, index)
        print(e.pack_info())

    def _dep__seek(self, index=None):
        e = list.__getitem__(self, index)
        e.pack_forget()


class ScrollableSessionDataView(ttk.Frame):
    def __init__(self, *args, visible_els=10, **kwargs):
        kw = dict(width=400, height=300) # base params
        kw.update(kwargs)
        super().__init__(*args, **kw)
        super().__init__(*args, **kwargs)
        self.scroll = ttk.Scrollbar(self, command=self.on_scroll)
        self.scroll.pack(fill='both', side='right')

        ttk.Style().configure('White.TFrame', background='white')

        self.view = SessionDataView(
            self,
            scroll_upd_callback=self.scroll.set,
            visible_els=visible_els,
            style='White.TFrame'
        )
        self.view.pack(expand=True, fill='both')  # , side='left')
        #self.view.pack_propagate(False)


    def on_scroll(self, *args, **kwargs):
        value_raw = float(args[1])
        self.view.set_yview(value_raw)


class Tableview(ttk.Treeview):
    class EntryPopup(ttk.Entry):
        def __init__(self, parent, iid, column, text, destroy_callback, sort_callback, **kw):
            ttk.Style().configure('pad.TEntry', padding='1 1 1 1')
            super().__init__(parent, style='pad.TEntry', **kw)
            self.tv = parent
            self.iid = iid
            self.column = column
            self.destroy_callback = destroy_callback
            self.sort_callback = sort_callback

            self.insert(0, text)
            # self['state'] = 'readonly'
            # self['readonlybackground'] = 'white'
            # self['selectbackground'] = '#1BA1E2'
            self['exportselection'] = False

            self.focus_force()
            self.select_all()
            self.bind("<Return>", self.on_return)
            self.bind("<FocusOut>", lambda *_: self.destroy_callback())
            self.bind("<Control-a>", self.select_all)
            self.bind("<Escape>", lambda *ignore: self.destroy())

        def on_return(self, event):
            rowid = self.tv.focus()
            if self.column == -1:
                self.tv.item(rowid, text=self.get())
            else :
                vals = self.tv.item(rowid, 'values')
                vals = list(vals)
                vals[self.column] = self.get()
                self.tv.item(rowid, values=vals)
            self.destroy_callback()
            self.sort_callback(rowid=rowid)

        def select_all(self, *ignore):
            ''' Set selection on the whole text '''
            self.selection_range(0, 'end')
            # returns 'break' to interrupt default key-bindings
            return 'break'

    class FocusItem:
        def __init__(self, widget, rowid=None, store_parent_id=False):
            self.widget = widget
            self._rowid = rowid
            self._get_parent_id = store_parent_id
            self._parent_id = None

        @property
        def rowid(self):
            res = None
            if self._rowid is None:
                res = self.widget.focus()
                self._cashed_rowid = str(res)
            else :
                res = self._rowid
            if self._get_parent_id:
                self._parent_id = self.widget.parent(res)
                self._get_parent_id = False
            return res

        @rowid.setter
        def rowid(self, value):
            self._rowid = value

        @property
        def parentid(self):
            return self._parent_id

        @property
        def cashed_rowid(self):
            return self._cashed_rowid

        @property
        def config(self):
            return self.widget.item(self.rowid)

        @property
        def item(self):
            return Item(**self.config, parent=self._parent_id, index=self.rowid)

        @property
        def is_base(self):
            return 'baseel' in self.config['tags']

        @property
        def is_dict(self):
            return 'is_dict' in self.config['tags']

        @property
        def is_editable(self):
            tags = self.config['tags']
            return 'internal' in tags or 'inserted' in tags

        @property
        def is_expandable(self):
            return 'expand' in self.config['tags']

        @property
        def is_internal(self):
            return 'internal' in self.config['tags']

    def __init__(self, *args,
                 first_column_name: str = None,
                 column_editable_matrix:tuple[bool] | None = None,
                 unacceptable_values: set| None = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.column_editable_matrix = column_editable_matrix
        if not first_column_name is None:
            self.insert('', 'insert_mode', text=first_column_name)
        self.unacceptable_values = set(['...', 'same'])
        if unacceptable_values is not None:
            self.unacceptable_values.add(unacceptable_values)
        self.entryPopup = None

        self.bind("<Double-1>", self.onDoubleClick)
        self.bind("<Shift-+>", self.on_add)
        self.bind("<Shift-Delete>", self.on_remove)
        self.bind("<Shift-Up>", self.on_arrow_up)
        self.bind("<Shift-Down>", self.on_arrow_down)

    def entry_destroy(self):
        if not self.entryPopup is None:
            self.entryPopup.destroy()
            self.entryPopup = None

    def expand_sort(self, rowid=None):
        itm = self.FocusItem(self, rowid=rowid)
        if itm.is_editable:
            rowid = self.parent(rowid)
        itm.rowid = rowid
        if not itm.is_expandable:
            print(f'such id ({rowid}) can not be sort')
            return
        if itm.is_dict:
            print(f'dict expand field can not be sort')
            return
        childrens = self.get_children(rowid)
        data = {i: self.item(i) for i in childrens}
        proxy__childrens = list(childrens)
        try:
            proxy__childrens.sort(key=lambda x: int(data[x]['text']))
        except ValueError as err:
            err_value = str(err).replace("invalid literal for int() with base 10: ","")
            print(f'one of the values is not Int ({err_value})')
            return
        for num, (proxy_id, base_id) in enumerate(zip(proxy__childrens, childrens)):
            conf = data[proxy_id]
            conf['text'] = str(num)
            self.item(base_id, **conf)
        pass



    def _item_recognition_by_pressed_coordinate(self, event):
        pass

    def _swap_internals(self, baseid, proxyid, is_dict=False):
        base_i = self.item(baseid)
        proxy_i = self.item(proxyid)
        if is_dict:
            proxy_text = proxy_i['text']
            base_text = base_i['text']
            base_i['text'] = proxy_text
            proxy_i['text'] = base_text
        self.item(proxyid, **base_i)
        self.item(baseid, **proxy_i)

    def on_arrow_up(self, event):
        itm = self.FocusItem(self)
        if itm.is_editable:
            rowid =itm.rowid
            expand_section_id = self.parent(rowid)
            is_dict = not 'is_dict' in self.item(expand_section_id, 'tags')
            childrens = self.get_children(expand_section_id)
            idx = childrens.index(rowid)
            if idx  == 0:
                print('such internal element placed on the top of expand section and can not be moved up!')
            if idx == -1:
                print('Unpredictable bechaviour')
            proxyid = childrens[idx-1]
            self._swap_internals(baseid=rowid,
                                 proxyid=proxyid,
                                 is_dict=is_dict)
        elif itm.is_expandable:
            print('can not replace expand field')

    def on_arrow_down(self, event):
        itm = self.FocusItem(self)
        if itm.is_editable:
            rowid =itm.rowid
            expand_section_id = self.parent(rowid)
            is_dict = not 'is_dict' in self.item(expand_section_id, 'tags')
            childrens = self.get_children(expand_section_id)
            idx = childrens.index(rowid)
            if idx  == len(childrens)-1:
                print('such internal element placed at the end of expand section and can not be moved down!')
            if idx == -1:
                print('Unpredictable behavior')
            proxyid = childrens[idx+1]
            self._swap_internals(baseid=rowid,
                                 proxyid=proxyid,
                                 is_dict=is_dict)
        elif itm.is_expandable:
            print('can not replace expand field')

    def on_add(self, event):
        """
        если элемент с тегом 'internal'
        то можно удалить или добавить в конец
        (сначала выделить, потом нажать ) т.е через self.focus()
        """
        itm = self.FocusItem(self)
        rowid =itm.rowid
        if itm.is_editable:
            print('can not insert into internal field')
        elif itm.is_expandable:
            last_num = 'test'
            type_ = 'same'
            if not itm.is_dict:
                try:
                    last_num_id = self.get_children(itm.rowid)[-1]

                    try:
                        value = self.item(last_num_id,'text')
                        last_num = int(value)+1
                        last_num = str(last_num)
                    except ValueError:
                        print(f'last_value in expand ({itm.config["text"]}) is not int({value})')
                        return
                except IndexError:
                    last_num = '0'
                type_ = 'same'

            self.insert(rowid, 'end', text=last_num, values=(type_, ''), tags=('inserted','internal'))
        self.expand_sort(rowid=rowid)


    def on_remove(self, event):
        itm = self.FocusItem(self, store_parent_id=True)
        if itm.is_editable:
            self.delete(itm.rowid)
        elif itm.is_expandable:
            print('can not remove expand field')
        self.expand_sort(rowid=itm.parentid)

    def onDoubleClick(self, event):
        ''' Executed, when a row is double-clicked. Opens
        read-only EntryPopup above the item's column, so it is possible
        to select text '''

        self.entry_destroy()
        # what row and column was clicked on
        rowid = self.identify_row(event.y)
        column = self.identify_column(event.x)
        #print(rowid,column)

        # handle exception when header is double click
        if not rowid:
            print(f'no {event.y} TreeView row is detected!')
            return

        column_num = int(column.replace('#',''))
        itm = self.FocusItem(self, rowid=rowid)
        idx__column = column_num -1

        if column_num == 0:
            if not itm.is_internal:
                print('Name (first) column - not editable!')
                return
        elif self.column_editable_matrix is not None and\
                not self.column_editable_matrix[idx__column] and\
                not itm.is_internal:
            print(f'{rowid} column {column} - not editable!')
            return

        # get column position info
        x,y,width,height = self.bbox(rowid, column)

        # y-axis offset
        pady = height // 2

        # place Entry popup properly
        try:
            if idx__column != -1:
                vals = itm.config['values']
                text = vals[idx__column]
            else :
                text = itm.config['text']
        except IndexError:
            print(f'{rowid} hasn\'t got value in column {column_num} (only {len(vals)})')
            return

        if text in self.unacceptable_values:
            print(f'such value ({text}) can not be changed')
            return
        #print(text)
        self.entryPopup = self.EntryPopup(self,
                                          rowid,
                                          idx__column,
                                          text,
                                          destroy_callback=self.entry_destroy,
                                          sort_callback= self.expand_sort)
        self.entryPopup.place(x=x,
                              y=y+pady,
                              width=width,
                              height=height,
                              anchor='w')


class StrategyView(Tableview):
    class StrategyViewColumnsConfig(dict):
        @property
        def data_columns(self):
            return [i for i in self['user_defined']]

        @property
        def data_columns_editability(self):
            return [i['editable'] for i in self['user_defined'].values()]

        @property
        def geometry_configuration(self):
            d = {'#0': self['#0']}
            d.update({
                key: value
                for key, value
                in self['user_defined'].items()
            })
            return d

        @property
        def tags(self):
            return self['tags']

    @dataclass(init=True)
    class StrategyViewRow:
        name: str = ''
        type: str = ''
        value: str = ''

        @classmethod
        def fromItem(cls, i: Item):
            type, value = i.values
            match value.strip():
                case 'False':
                    value = False
                case 'True':
                    value = True
                case 'None':
                    value = None
            return cls(i.text, type, value)

    def __init__(self, root, raw_config: dict):
        self.columns_config = (conf := self.StrategyViewColumnsConfig(raw_config))
        super().__init__(root,
                         column_editable_matrix=conf.data_columns_editability,
                         columns=conf.data_columns)
        self._configure_columns()
        self._configure_tags()

    def _configure_columns(self):
        for identification, data in self.columns_config.geometry_configuration.items():
            self.column(identification, **data['column'])
            self.heading(identification, **data['heading'])

    def _configure_tags(self):
        for name, conf in self.columns_config.tags.items():
            self.tag_configure(name, **conf)

    def insert_dict(self, val: Item):
        return self.insert(**asdict(val))

    def clear_widget(self):
        for itemid in self.get_children('')[::-1]:
            itm = self.FocusItem(self, rowid=itemid)
            if itm.is_editable:
                continue
            self.delete(itm.rowid)

    def reset_strategy(self):
        if self._cashed_strategy is not None:
            self.clear_widget()
            self._insert_strategy(strat=self._cashed_strategy)
        else :
            print('Strategy hasnt been previously inserted...')

    def insert_strategy(self, strat: Strategy):
        self._cashed_strategy = strat
        self.clear_widget()
        self._insert_strategy(strat=strat)
        print(self._cashed_strategy)

    def _insert_strategy(self, strat: Strategy):
        expand_field = Strategy.expand_fields
        strat_dict = asdict(strat)
        if strat.is_value:
            strat_dict = { key:strat_dict[key] for key in Strategy.value_repr_keys }
        fields_ = {f.name:f for f in fields(strat)}
        iterable_ = ((key, fields_[key], strat_dict[key]) for key in strat_dict.keys())
        for key, field_, value in iterable_:
            i = Item(
                text=field_.name,
                values=(str(field_.type), value),
                tags=('baseel',)
            )
            is_expand = i.text in expand_field \
                        and not isinstance(value, str) \
                        and value is not None
            if is_expand:
                i.values = (i.values[0], '...')
                i.open = True
                i.tags = ('expand',)
            is_dict = isinstance(value, dict)
            if is_dict:
                i.tags = (*i.tags, 'is_dict')
            id = self.insert(**asdict(i))
            if is_expand:
                iterable = [(str(num), i) for num, i in enumerate(value)]
                if is_dict:
                    iterable = [i for i in value.items()]

                for name, value_ in iterable:
                    i_ = Item(
                        parent=id,
                        text=name,
                        values=('same', value_),
                        tags=('internal',)
                    )
                    self.insert(**asdict(i_))

    def extract_strategy(self) -> Strategy:
        try:
            strat = self._extract_strategy()
            self._cashed_strategy = None
            self.clear_widget()
            return strat
        except BaseException as err:
            print(f'(manual) Strategy cannot be extracted ({err})')

    def _extract_strategy(self) -> Strategy:
        # row model
        expand_field = Strategy.expand_fields
        strat = {}
        for itemid in self.get_children(''):
            itm = self.FocusItem(self, rowid=itemid)
            row = self.StrategyViewRow.fromItem(itm.item)
            if itm.is_base:
                strat[row.name] = row.value
            elif itm.is_expandable:
                children = self.get_children(itm.rowid)
                data = [self.StrategyViewRow.fromItem(Item(**self.item(id_))) for id_ in children]
                if itm.is_dict:
                    data = {row_.name: row_.value for row_ in data}
                else:  # is list
                    data = [row_.value for row_ in data]
                strat[row.name] = data
            elif itm.is_editable:
                continue
        return Strategy.fromdict(strat)


class ChoseCombobox(ttk.Frame):
    def __init__(self, *args, name='', action_name='', init_value= '', **kw):
        super().__init__(*args, **kw)
        self.label = ttk.Label(self, text=name)
        self.var = StringVar(self, value=init_value)
        self.entry = ttk.Entry(self, textvariable=self.var)
        self.button = ttk.Button(self, text=action_name)

    def place_internals(self):
        base = {'expand': True, 'fill': 'x', 'side':'left'}
        self.label.pack(fill='x', side='left')
        self.entry.pack(**base)
        self.button.pack(fill='x', side='left')


class StatusIndicator(ttk.Label):
    pixel_per_symbol_ratio = 600/100
    def __init__(self, *args, delay=3, **kwargs):
        super().__init__(*args, **kwargs)
        self.delay = delay

    def _continue_indication(self, init_colour):
        self.configure(background=init_colour)
        sleep(self.delay)
        self.configure(background='')

    @property
    def _symbol_line_limit(self):
        width = self.winfo_width()
        raw = width / self.pixel_per_symbol_ratio
        return int(raw)

    def _separate_text_by_available_width(self, text:str):
        class SpecLineList(list):
            def append(self, value: list[str]):
                super().append(' '.join(value))

            def __str__(self):
                return '\n'.join(self)

        parts = SpecLineList()
        line = []
        words = text.split(' ')
        curr_len = 0
        for word in words:
            word_len = len(word) + 1  # пробел
            curr_len += word_len
            if curr_len > self._symbol_line_limit:
                parts.append(line)
                curr_len = word_len
                line = [word]
            else:
                line.append(word)
        else:
            parts.append(line)  # спрятанное преобразование list[str] -> space separate str
        return str(parts)

    def process_status(self, stt: OperationStatus):
        sep_text = self._separate_text_by_available_width(stt.description)
        self.configure(text= sep_text) #'\n' working in label
        threading.Thread(target=self._continue_indication, args=(stt.color_by_state,)).start()


#dep
class ConfigDirectoryChoseCombobox(ChoseCombobox):
    def __init__(self, *args,
                 init_folder_value = '',
                 status_upd_callback= None,
                 export_data_callback= None,
                 **kw):
        super().__init__(*args,
                         name='Config directory',
                         action_name='выбрать',
                         **kw)
        self.status_upd = status_upd_callback if status_upd_callback is not None else lambda x: x
        self.export_data_callback = export_data_callback if export_data_callback is not None else lambda x: x
        self.button.configure(command=self.on_dirchoose)
        #self.var.trace_add('write', self.path_validation) #исправить через валидацию
        self.bind('<FocusOut>', self.path_validation)
        self.var.trace_add('write', self.send_upd)


    def send_upd(self, *_):
        self.export_data_callback(self.acceptable_files)

    def on_dirchoose(self, *_):
        path = askdirectory()
        if self.path_validation(path):
            self.var.set(path)

    @property
    def acceptable_files(self) -> list[pathlib.Path]:
        path = self.var.get()
        if path != '':
            return [
                i
                for i in pathlib.Path(path).iterdir()
                if i.suffix.lower() == '.json'
            ]
        return []

    def path_is_acceptable(self) -> bool:
        path = self.var.get()
        return pathlib.Path(path).exists()

    def path_validation(self, *_, path=None) -> bool:
        path = self.var.get() if path is None else path
        is_ = pathlib.Path(path).exists()
        if is_:
            stt = OperationStatus(
                description=f'Path ({path}) - exists',
                flag='accepted'
            )
        else :
            stt = OperationStatus(
                description=f'Path ({path}) - does not exist',
                flag='denied'
            )
            self.var.set('')
        self.status_upd(stt)
        return is_


class LabelDialog(tk.Toplevel):
    @dataclass
    class Data:
        text: str = ''
        is_: bool = False

    def __init__(self, *args,
                 text='',
                 export_data_callback= lambda *_ : None,
                 **kw):
        super().__init__(*args, **kw)
        self.label = ttk.Label(self, text=text)
        self.var = tk.StringVar(value='')
        self.entry = ttk.Entry(self, textvariable=self.var)
        self.ac_bt = ttk.Button(self, text='ok', command=self.on_accept)
        self.cl_bt = ttk.Button(self, text='cancel', command=self.on_denied)

        #ttk.Style().configure()
        self.on_export = export_data_callback
        self.geometry('400x120+400+200')
        self.entry.bind('<Return>', self.on_accept)

    def on_accept(self, *_):
        self.destroy()
        self.on_export(self.Data(text=self.var.get(), is_=True))

    def on_denied(self, *_):
        self.destroy()
        self.on_export(self.Data(text=self.var.get(), is_=False))

    def place_internals(self):
        self.label.pack(expand=True, fill='x', anchor='center')
        self.entry.pack(expand=True, fill='x')
        self.ac_bt.pack(side='left', anchor='center')
        self.cl_bt.pack(side='right', anchor='center')


class EditLabelCombobox(ttk.Frame, metaclass=ABCMeta):
    class UsrStringVar(StringVar):
        def get(self):
            val = super().get()
            if val == 'None':
                return None
            return val

    def __init__(self, *args,
                 text='',
                 initial_export_data_callback= lambda *_: None,
                 export_data_callback = lambda *_: None,
                 save_changes_callback =lambda *_: None,
                 **kw):
        super().__init__(*args, **kw)
        self.initial_export_data_callback = initial_export_data_callback
        self.export_data_callback = export_data_callback
        self.save_changes_callback = save_changes_callback
        self.var = self.UsrStringVar(value='')
        self.box = ttk.Combobox(self, textvariable=self.var, state='readonly')
        self.label = ttk.Label(self, text=text)
        self.add_bt = ttk.Button(self, text= "+", command=self.add_empty_element, style='add.TButton')
        self.rm_bt = ttk.Button(self, text= "-", command=self.remove_element, style='remove.TButton')
        self.var.trace_add('write', self.send_upd)
        self.input_values = None
        self.cashed = None

    @abstractmethod
    def remove_element(self, *_):
        pass

    @abstractmethod
    def add_empty_element(self, *_):
        pass

    def _plug(self, *_):
        showerror('Callback', 'no mapping func avaluable!')

    def send_upd(self, *_):
        val = self.var.get()
        self.export_data_callback(val)

    def update_view(self, new: list[str], value= None) -> None:
        self.box.configure(values=new)
        try:
            ch_val = new[0]
            if value is not None:
                search = [i for i in new if i==value]
                assert len(search) > 0, f'Manual. Chosen unacceptable value for {self.__class__.__name__} widget'
                ch_val = value
            self.var.set(ch_val)
        except IndexError:
            self.var.set('None')
        except AssertionError:
            raise

    def place_internals(self):
        self.label.pack(side='left', fill='x')
        self.box.pack(expand=True, side='left', fill='x')
        self.add_bt.pack(side='left')
        self.rm_bt.pack(side='left')


class ConfigLabelCombobox(EditLabelCombobox):
    def update_values(self, new: ConfigurationSelectChain) -> None:
        self.cashed = new
        try:
           self.update_view(new = list(self.cashed.base_jsons.keys()),
                             value= self.cashed.selected_parser)
        except AssertionError:
            self.cashed.selected_parser = None
            self.update_view(new=list(self.cashed.base_jsons.keys()))

    def send_upd(self, *_):
        cur_value = self.var.get()
        self.cashed.selected_parser = cur_value
        try:
            templ_parser_type: type = self.cashed.base_jsons[cur_value]
            templ_parser_obj: object = templ_parser_type()
            self.cashed.parser_obj = templ_parser_obj
        except KeyError:
            self.cashed.parser_obj = None
        self.export_data_callback(self.cashed)

    def remove_element(self, *_):
        #по сути удалить файл
        # dialog requvierd
        self._plug()
        self.initial_export_data_callback()

    def _add_empty_element(self, data):
        self._plug()
        self.initial_export_data_callback()

    def add_empty_element(self, *_):
        lb = LabelDialog(text='New parser name:', export_data_callback=self._add_empty_element)
        lb.place_internals()


class ExtractorLabelCombobox(EditLabelCombobox):
    def update_values(self, new: ConfigurationSelectChain ) -> None:
        """by (new =) StrategyParserConfigurationManager.TemplParser.create method"""
        self.cashed = new
        try:
            self.update_view(new = self.cashed.parser_obj.__extractors__,
                             value=self.cashed.selected_extractor)
        except AssertionError:
            self.cashed.selected_extractor = None
            self.update_view(new = self.cashed.parser_obj.__extractors__)

    def send_upd(self, *_):
        cur_value = self.var.get()
        self.cashed.selected_extractor = cur_value
        if cur_value is not None:
            templ_extractor: type = getattr(self.cashed.parser_obj, cur_value)
            templ_extractor: object = templ_extractor()
            self.cashed.extractor_obj = templ_extractor
        else :
            self.cashed.extractor_obj = None
        self.export_data_callback(self.cashed)

    def remove_element(self, *_):
        assert askquestion('Удаление стратегии',
                           f'Вы действительно желаете удалить\n экстрактор "{self.cashed.selected_extractor}"?') == 'yes', 'отмена удаления'
        assert self.cashed.selected_extractor is not None, 'Невозможно удалить <NoneType> стратегию'
        print(f'Удаляю стратегию "{self.cashed.selected_extractor}" из объекта парсера "{self.cashed.selected_parser}"')

        self.cashed.parser_obj.__extractors__.remove(self.cashed.selected_extractor)
        self.save_changes_callback()
        self.update_values(self.cashed)
        self.send_upd()

    def _add_empty_element(self, data):
        name = data.text
        assert data.is_, 'add_empty_element denied'
        self.cashed.parser_obj.__extractors__.append(name)
        setattr(self.cashed.parser_obj.__class__, name, self.cashed.extractor_obj.create_empty(name=name))
        self.cashed.selected_extractor = name
        self.save_changes_callback()
        self.update_values(self.cashed)
        self.send_upd()

    def add_empty_element(self, *_):
        lb = LabelDialog(text='New extractor name:', export_data_callback=self._add_empty_element)
        lb.place_internals()


class StrategyLabelCombobox(EditLabelCombobox):
    def update_values(self, new: ConfigurationSelectChain) -> None:
        """by (new =) StrategyParserConfigurationManager.TemplParser.TemplExtractor.create method"""
        self.cashed = new
        try:
            self.update_view(new = self.cashed.extractor_obj.__strategies__,
                             value=self.cashed.selected_strategy)
        except AssertionError:
            self.cashed.selected_strategy = None
            self.update_view(new = self.cashed.extractor_obj.__strategies__)

    def send_upd(self, *_):
        cur_value = self.var.get()
        self.cashed.selected_strategy = cur_value

        if cur_value is not None:
            cashed_strategy_obj: CashedStrategy = self.cashed.extractor_obj.\
                get_base_attr(cur_value)
            strategy_obj: Strategy = self.cashed.extractor_obj.\
                get_strategy_from_base_attr(cur_value)
            # if strategy_obj is None - field is value
            # nessessary to hard coded value in config
            # (extractor not acceptable to have predefined fields)
            # = full chaos
            self.cashed.cashed_strategy_obj = cashed_strategy_obj
            self.cashed.strategy_obj = strategy_obj
        else :
            self.cashed.cashed_strategy_obj = None
            self.cashed.strategy_obj = None

        self.export_data_callback(self.cashed)

    def remove_element(self, *_):
        #pdb.set_trace()
        # можно удалить через delattr если не при создании объекта аттрибуты передаются
        assert askquestion('Удаление стратегии', f'Вы действительно желаете удалить\n статегию "{self.cashed.selected_strategy}"?') == 'yes', 'отмена удаления'
        assert self.cashed.selected_strategy is not None, 'Невозможно удалить <NoneType> стратегию'
        print(f'Удаляю стратегию "{self.cashed.selected_strategy}" из объекта экстрактора "{self.cashed.selected_extractor}"')

        self.cashed.extractor_obj.__strategies__.remove(self.cashed.selected_strategy)
        self.cashed.cashed_strategy_obj = None
        self.cashed.strategy_obj = None
        self.cashed.selected_strategy = None
        self.save_changes_callback()
        self.update_values(self.cashed)
        self.send_upd()

    def _add_empty_element(self, data: LabelDialog.Data):
        name = data.text
        assert data.is_, 'add_empty_element denied'
        print(f'Добавляю стратегию "{name}" в объект экстрактора "{self.cashed.selected_extractor}"')
        self.cashed.extractor_obj.__strategies__.append(name)
        setattr(self.cashed.extractor_obj.__class__, name, self.cashed.extractor_obj.element_type.create_empty())
        self.cashed.selected_strategy = name
        self.save_changes_callback() #вся цепочка обновляется, поэтому сначала сохранить, потом обновить

        self.update_values(self.cashed)
        self.send_upd()

    def add_empty_element(self, *_):
        lb = LabelDialog(self, text='New strategy name:', export_data_callback=self._add_empty_element)
        lb.place_internals()



class ConfigurationManager(ttk.LabelFrame):
    def __init__(self,
                 *args,
                 status_upd_callback = lambda *_: None,
                 strategy_export_callback = lambda *_: None,
                 save_changes_callback = lambda *_: None,
                 **kw):
        self.save_changes_callback = save_changes_callback
        self.strategy_export_callback = strategy_export_callback
        super().__init__(*args, text = 'Configuration', **kw)
        #add_callback = self._plug, rm_callback = self._plug
        self.strategy = StrategyLabelCombobox(self, text='Strategy', export_data_callback=self.strategy_export_callback, save_changes_callback=self.save_changes_callback)#, add_callback = self._plug, rm_callback = self._plug)
        self.extractor = ExtractorLabelCombobox(self, text='Extractor', export_data_callback=self.strategy.update_values, save_changes_callback=self.save_changes_callback)#, add_callback = self._plug, rm_callback = self._plug)
        self.config = ConfigLabelCombobox(self, text='File', export_data_callback=self.extractor.update_values, save_changes_callback=self.save_changes_callback)#, add_callback = self._plug, rm_callback = self._plug)
        self.strategy.initial_export_data_callback = self.config.send_upd
        self.extractor.initial_export_data_callback = self.config.send_upd


    def update_values(self, init_value):
        #separate to prevent run befoure tk.Tk var variable will be created
        self.config.update_values(init_value)

    def place_internals(self):
        base = {'expand': True, 'fill': 'x'}
        for itm in [self.config , self.extractor, self.strategy]:
            itm.pack(**base)
            itm.place_internals()




