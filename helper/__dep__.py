
from . import Tk, Tableview

def last_app() -> Tk:
    root = Tk()
    tv = root
    tree = Tableview(root)
    tree['columns'] = ('size', 'modify', 'owner')
    for col_name in tree['columns']:
        tree.column(col_name, width=100, anchor='center')
        tree.heading(col_name, text=col_name.capitalize())


    tree.grid(sticky='swen')

    #Inserted at the root, program chooses id:
    tree.insert('', 'end', 'widgets', text='Widget Tour')
    # Same thing, but inserted as first child:
    tree.insert('', 0, 'gallery', text='Applications')
    # Treeview chooses the id:
    id = tree.insert('', 'end', text='Tutorial')
    # Inserted underneath an existing node:
    tree.insert('widgets', 'end', text='Canvas')
    tree.insert(id, 'end', text='Tree')

    tree.move('widgets', 'gallery', 'end')



    tree.set('widgets', 'size', '12KB')
    size = tree.set('widgets', 'size')
    tree.insert('', 'end', text='Listbox', values=('15KB', 'Yesterday', 'mark'))
    tree.insert(id, 'end', text='Listbox', values=('15KB', 'Yesterday', 'mark'))

    tree.insert('', 'end', text='button', tags=('ttk', 'simple'))
    tree.tag_configure('ttk', background='yellow')
    tree.tag_bind('ttk', '<1>', "itemClicked")
    # the item clicked can be found via tree.focus()

    return root
