'''TabList 

A listbox that serves as the list of tabs for a notebook. One notable
feature is that it maintains its items in alphabetical order. At least,
it did when I wrote this comment.
'''

import ttk
import Tkinter as tk
import re
#import core.colors

class ListItem(object):
    def __init__(self, name, object):
        self.item_id = None
        self.name = name
        self.object=object

        # the sort key is the name split into strings and integers.
        # the reason? So that a file like "foo10" appears after "foo2"
        # in sort order 
        self.sort_key = [self._int_or_string(span) for span in re.split('([0-9]+)', name)]

    def _int_or_string(self, text):
        '''Return int if text is all digits, otherwise return a string'''
        return int(text) if text.isdigit() else text

class TabList(ttk.Frame):
    def __init__(self, *args, **kwargs):
        ttk.Frame.__init__(self, *args, **kwargs)
        self._listbox = ttk.Treeview(self)
        self._listbox.pack(side="top", fill="both", expand=True, padx=(0,0))
        self._listbox.bind("<<TreeviewSelect>>", self._on_listbox_select)
        self._list_items = {}
        self._map = {}

        self.xview = self._listbox.xview
        self.yview = self._listbox.yview
        self.configure = self._listbox.configure

    def get(self):
        '''Get the object of the currently selected item'''

        selection = self._listbox.selection()
        if selection is not None and len(selection) > 0:
            item_id = selection[0]
            item = self._list_items[item_id]
            return item.name, item.object
        return (None, None)

    def add(self, text, object):
        '''Add an object to the list'''
        list_item = ListItem(text, object)
        list_item.item_id = self._listbox.insert("", "end", text=text)
        self._list_items[list_item.item_id] = list_item
        self._sort_list()
        self._select(list_item.item_id)

    def _sort_list(self):
        sorted_items = sorted(self._list_items.values(), key=lambda item: item.sort_key)
        for index, item in enumerate(sorted_items):
            self._listbox.move(item.item_id, '', index)

    def rename(self, object):
        i = self._get_object_index(object)
        if i is not None:
            self._listbox.delete(i)
            self._listbox.insert(i, " - " + object.name)
            self._listbox.selection_set(i)

    def remove(self, object):
        '''Remove an object from the list'''
        print "remove:", object
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
        for item in self._listbox.selection():
            self._listbox.selection_remove(item)
        self._listbox.selection_set(index)
