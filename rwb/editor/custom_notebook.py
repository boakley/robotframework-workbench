'''Tree-based  Notebook

TODO: decouple the notebook from the listbox. Let them communicate
via events, or have them work together via an interface (eg:
notebook.configure(tablist=self.tablist)
'''

import os
import Tkinter as tk
import ttk
from rwb.widgets import AutoScrollbar
from editor_page import EditorPage
from tablist import TabList

# orange and gray colors taken from
# http://www.colorcombos.com/color-schemes/218/ColorCombo218.html

class CustomNotebook(tk.Frame):
    def __init__(self, parent, app=None):
        tk.Frame.__init__(self, parent)
        background = self.cget("background")
        self.app = app
        self.pages = []
        self.nodelist = []
        self.current_page = None

        # within the frame are two panes; the left has a tree,
        # the right shows the current page. We need a splitter
        self.pw = tk.PanedWindow(self, orient="horizontal", background="#f58735", 
                                 borderwidth=1,relief='solid',
                                 sashwidth=3)
        self.pw.pack(side="top", fill="both", expand=True, pady = (4,1), padx=4)
        self.left = tk.Frame(self.pw, background=background, borderwidth=0, highlightthickness=0)
        self.right = tk.Frame(self.pw, background="white", width=600, height=600, borderwidth=0, 
                              highlightthickness=0)
        self.pw.add(self.left)
        self.pw.add(self.right)

        self.list = TabList(self.left)
        vsb = AutoScrollbar(self.left, command=self.list.yview, orient="vertical")
        hsb = AutoScrollbar(self.left, command=self.list.xview, orient="horizontal")
        self.list.configure(xscrollcommand=hsb.set, yscrollcommand=vsb.set)

        self.list.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        vsb.grid(row=0, column=0, sticky="ns")
        hsb.grid(row=1, column=1, sticky="ew")
        self.left.grid_rowconfigure(0, weight=1)
        self.left.grid_columnconfigure(1, weight=1)
        self.list.bind("<<ListboxSelect>>", self.on_list_selection)

    def get_current_page(self):
        return self.current_page

    def on_list_selection(self, event):
        page = self.list.get()[1]
        self._select_page(page)

    def delete_page(self, page):
        print __file__, "delete_page is presently under development..."
        if page in self.pages:
            self.pages.remove(page)
            self.list.remove(page)
            selection = self.list.get()
            page.pack_forget()
            page.destroy()
#            if selection is not None and len(selection) > 0:
#                self.select_page(selection[1])

    def _page_name_changed(self, page):
        self.list.rename(page)

    def get_page_by_name(self, name):
        for page in self.pages:
            if page.name == name:
                return page
        return None

    def get_page_for_path(self, path):
        target_path = os.path.abspath(path)
        for page in self.pages:
            if page.path == target_path:
                return page
        return None

    def add_custom_page(self, page_class):
        new_page = page_class(self.right)
        self.pages.append(new_page)
        self.list.add(new_page.name, new_page)
        self._select_page(new_page)
        return new_page

    def add_page(self, path=None, name=None):
        if path is None and name is None:
            raise Exception("you must specify either a path or a name")
        if path is not None and name is not None:
            raise Exception("you cannot specify both a path and a name")

        new_page = EditorPage(self.right, path, name=name, app=self.app)
        new_page.bind("<<NameChanged>>", lambda event, page=new_page: self._page_name_changed(page))
        self.pages.append(new_page)
        self.list.add(new_page.name, new_page)
        self._select_page(new_page)
        return new_page

    def select_page(self, page):
        self.list.select(page)

    def _select_page(self, page):
        for p in self.pages:
            p.pack_forget()
        if page is not None:
            page.pack(fill="both", expand=True, padx=4, pady=0)
            self.after_idle(page.focus)
        self.current_page = page
        return page
