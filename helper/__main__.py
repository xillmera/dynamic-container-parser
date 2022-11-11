from src.__stable_prepared.helper import (
    last_app, App
)

from src.__stable_prepared.helper.input import (
    TestData
)

from sys import argv
import pathlib
import json


def get_raw_config():
    p = pathlib.Path(__file__).parent / 'config.json'
    d = p.read_text(encoding='utf-8')
    j = json.loads(d)
    return j


if 'v1' in argv:
    last_app().mainloop()
elif 'v2' in argv:
    strats = TestData.strats()
    app = App(global_config=get_raw_config())
    #app.vars['strategyView'].insert_strategy(strats[0])
    app.place()
    app.mainloop()
