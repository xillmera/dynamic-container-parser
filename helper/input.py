from . import Item, Strategy

items = [
    {
        'text':'Listbox',
        'values':('15KB', 'Yesterday', 'mark')
    },
    {
        'text':'Widget Tour',
        'iid':'widgets'
    },
    {
        'text':"Application",
        'index':0,
        'iid':'gallery'
    },
    {
        'text':'Tutorial',
        'iid':'toot'
    },
    {
        'parent':'toot',
        'text':'Canvas'
    },
    {
        'parent':'toot',
        'text':'Canvas'
    },
    {
        'parent':'toot',
        'text':'Tree'
    }
]

strats = {
    'description_full':{
		"initial": "target_content.soup",
		"config_sequence": [
			"recv.one@sel_1@sel.soup",
			"recv.multi@sel_2@sel.soup_list",
			"proc.text_multiline.res"
		],
		"context": {
			"sel_1": ".post-header__body",
			"sel_2": "div.editor-content > p"
		}
	}
}

class TestData:
    @classmethod
    def items(cls) -> list[Item]:
        global items
        return [Item(**i) for i in items]

    @classmethod
    def strats(cls) -> list[Strategy]:
        global strat
        return [Strategy(**strats['description_full'])]