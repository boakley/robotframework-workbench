'''TabList 

A listbox that serves as the list of tabs for a notebook. One notable
feature is that it maintains its items in alphabetical order. At least,
it did when I wrote this comment.
'''

import ttk
import Tkinter as tk
#import core.colors

class ListItem(object):
    def __init__(self, name, object):
        self.name = name
        self.object=object

class TabList(ttk.Frame):
    def __init__(self, *args, **kwargs):
        ttk.Frame.__init__(self, *args, **kwargs)
        heading = tk.Label(self, text="Opened files", anchor="w")
#                            background=core.colors.background2, 
#                            foreground=core.colors.foreground2)
        self._listbox = tk.Listbox(self, borderwidth=0, 
                                   highlightthickness=0, activestyle="none",
                                   exportselection=False,
#                                   foreground=core.colors.foreground1,
#                                   selectbackground=core.colors.accent,
                                   selectmode="browse",
                                   width=32)

        heading.pack(side="top", fill="x", expand=False)
        self._listbox.pack(side="top", fill="both", expand=True, padx=(0,0))
        self._listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
        self._list_items = []
        self._map = {}

        self.xview = self._listbox.xview
        self.yview = self._listbox.yview
        self.configure = self._listbox.configure

    def get(self):
        '''Get the object of the currently selected item'''

        selection = self._listbox.curselection()
        if selection is not None and len(selection) > 0:
            index = int(selection[0])
            item = self._list_items[index]
            return (item.name, item.object)
        return (None, None)

    def add(self, text, object):
        '''Add an object to the list'''
        list_item = ListItem(text, object)
        self._list_items.append(list_item)
        self._list_items = sorted(self._list_items, key=lambda x: x.name)
        index = self._list_items.index(list_item)
        self._listbox.insert(index, " - " + text)
        self._select(index)

    def rename(self, object):
        i = self._get_object_index(object)
        if i is not None:
            self._listbox.delete(i)
            self._listbox.insert(i, " - " + object.name)
            self._listbox.selection_set(i)

    def remove(self, object):
        '''Remove an object from the list'''
        index = self._get_object_index(object)
        if index is not None:
            self._list_items.pop(index)
            selection = self._listbox.curselection()
            self._listbox.delete(index)
            if len(selection) > 0:
                i = int(selection[0])
                self._select(i)
        else:
            print "remove WTF?", object

    def select(self, key):
        '''Select an item in the list

        'key' can be either an integer index into the tree, or
        it can be an object associated with one of the rows in 
        the tree.
        '''

        if isinstance(key, int):
            target_object = self._list_items[int].object
        else:
            target_object = key

        for i, list_item in enumerate(self._list_items):
            if list_item.object is target_object:
                self._select(i)
                break

    def _on_listbox_select(self, *args):
        '''Called when the user selects an item from the tree'''
        self.event_generate("<<ListboxSelect>>")

    def _get_object_index(self, target_object):
        '''Return the index for the item associated with the given object'''
        for index, list_item in enumerate(self._list_items):
            if list_item.object is target_object:
                return index
        return None

    def _select(self, index):
        self._listbox.selection_clear(0, "end")
        self._listbox.selection_anchor(index)
        self._listbox.selection_set(index)
        self.event_generate("<<ListboxSelect>>")

t=None
def demo():
    global t
    root = tk.Tk()
    t = TabList(root)
    t.pack(side="top", fill="y")
    t.add("Label C", "label C")
    t.add("Label A", "label A")
    t.add("Label B", "label B")
