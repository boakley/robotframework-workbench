'''TabList 

A listbox that serves as the list of tabs for a notebook. One notable
feature is that it maintains its items in alphabetical order. At least,
it did when I wrote this comment.
'''

import ttk
import Tkinter as tk
import re
from rwb.widgets import TreeviewTooltip
#import core.colors

class ListItem(object):
    def __init__(self, item_id, name, editor_page):
        self.item_id = item_id
        self.name = name
        self.editor_page=editor_page

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
        self._listbox = ttk.Treeview(self, columns=("fullpath",), displaycolumns=[])
        self._listbox.pack(side="top", fill="both", expand=True, padx=(0,0))
        self._listbox.bind("<<TreeviewSelect>>", self._on_listbox_select)
        self._list_items = {}
        self._map = {}

        self.tooltip = TreeviewTooltip(self._listbox, callback=self._get_tooltip)
        self.xview = self._listbox.xview
        self.yview = self._listbox.yview
        self.configure = self._listbox.configure

    def _get_tooltip(self, element):
        list_item = self._list_items.get(element, None)
        if list_item is not None:
            path = list_item.editor_page.path
            return path
        return ""

    def _item_id(self, object):
        return "I%d" % id(object)

    def get(self):
        '''Get the object of the currently selected item'''

        selection = self._listbox.selection()
        if selection is not None and len(selection) > 0:
            item_id = selection[0]
            item = self._list_items[item_id]
            return item.name, item.editor_page
        return (None, None)

    def add(self, text, editor_page):
        '''Add an editor_page to the list'''
        item_id = self._item_id(editor_page)
        list_item = ListItem(item_id, text, editor_page)
        self._listbox.insert("", "end", iid=item_id, text=text)
        self._list_items[item_id] = list_item
        self._sort_list()

    def _sort_list(self):
        sorted_items = sorted(self._list_items.values(), key=lambda item: item.sort_key)
        for index, item in enumerate(sorted_items):
            self._listbox.move(item.item_id, '', index)

    def rename(self, editor_page):
        i = self._get_editor_page_index(editor_page)
        if i is not None:
            self._listbox.delete(i)
            self._listbox.insert(i, " - " + editor_page.name)
            self._listbox.selection_set(i)

    def remove(self, editor_page):
        '''Remove an editor_page from the list'''
        index = self._get_editor_page_index(editor_page)
        if index is not None:
            self._list_items.pop(index)
            selection = self._listbox.curselection()
            self._listbox.delete(index)
            if len(selection) > 0:
                i = int(selection[0])
                self._select(i)

    def select(self, key):
        '''Select an item in the list

        'key' can be either an integer index into the tree, or
        it can be an editor_page associated with one of the rows in 
        the tree.
        '''

        if isinstance(key, int):
            target_editor_page = self._list_items[int].editor_page
        else:
            target_editor_page = key

        for i, list_item in enumerate(self._list_items.values()):
            if list_item.editor_page is target_editor_page:
                self._listbox.selection_set((list_item.item_id))
#                self._select(i)
                break

    def _on_listbox_select(self, *args):
        '''Called when the user selects an item from the tree'''
        self.event_generate("<<ListboxSelect>>")

    def _get_editor_page_index(self, target_editor_page):
        '''Return the index for the item associated with the given editor_page'''
        for index, list_item in enumerate(self._list_items):
            if list_item.editor_page is target_editor_page:
                return index
        return None

    def _select(self, index):
        for item in self._listbox.selection():
            self._listbox.selection_remove(item)
        self._listbox.selection_set(index)
