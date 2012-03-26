'''KeywordTool - a tool for viewing keyword documentaton'''

import Tkinter as tk
import ttk
from rwb.widgets import AutoScrollbar, SearchBox
from rwb.lib import ColorScheme, FontScheme, KeywordTable

ALL_ID = ""
class KwBrowser(ttk.Frame):
    '''A widget designed to view keyword documentation'''
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.colors = ColorScheme()
        self.fonts = FontScheme()
        self.kwdb = KeywordTable()

        self._create_ui()
        self.reset()
        self.bind("<Visibility>", self._on_visibility)
        self.keyword_tree.bind("<<TreeviewSelect>>", self._on_list_select)
        self.lib_tree.bind("<<TreeviewSelect>>", self._on_lib_select)
        item = self.lib_tree.insert("", "end", text="All", values=[ALL_ID])
        self.lib_tree.selection_set(item)

    def reset(self):
        '''Reset the widgets and database to their startup state'''
        self.text.delete("1.0", "end")
        children = self.keyword_tree.get_children("")
        if len(children) > 0:
            self.keyword_tree.delete(*children)

        children = self.lib_tree.get_children("")
        if len(children) > 0:
            self.lib_tree.delete(*children)
        self.kwdb.reset()

    def search(self):
        '''Perform a search based on the criteria in the filter widget

        I should move this into the keywordtable object...
        '''
        type = self.filter.get_type()
        string = self.filter.get_string().lower()
        children = self.keyword_tree.get_children("")
        self.keyword_tree.delete(*children)
        library_selection = self.lib_tree.selection()

        library_id = ALL_ID
        if len(library_selection) > 0:
            item = library_selection[0]
            library = self.lib_tree.item(item, "text")
            library_id = self.lib_tree.item(item, "values")[0]
            
        # UGH. This is klunky. I should refactor this.
        pattern = "%" + string + "%"
        parameters = []
        SQL = ["SELECT kw.name, kw.id, kw.doc, c.name",
               "FROM keyword_table as kw",
               "JOIN collection_table as c",
               ]
        if type == "name":
            SQL.append("WHERE kw.name LIKE ?")
            parameters.append(pattern)
        else:
            SQL.append("WHERE (kw.name like ? OR kw.doc like ?)")
            parameters.append(pattern)
            parameters.append(pattern)

        if library_id != ALL_ID:
            SQL.append("AND c.id = ?")
            parameters.append(str(library_id))
            
        SQL.append("AND kw.collection_id == c.id")
        sql_result = self.kwdb.execute("\n".join(SQL), parameters)

        keywords = sql_result.fetchall()
        first = None
        for (name, kw_id, doc, source) in sorted(keywords, key=lambda t: t[0].lower()):
            description = doc.split("\n")[0]
            item = self.keyword_tree.insert("", "end", text=name,values=(kw_id, source, description))
            if first is None: first = item
        if first is None:
            self.text.delete(1.0, "end")
        else:
            self.keyword_tree.selection_set(first)

    def add_library(self, name, *args):
        '''Add all the keywords for the given library

        This will load the library using the given args.
        '''
        self.kwdb.add_library(name, *args)
        self._update_lib_tree()

    def add_file(self, filename):
        '''Add documentation for all keywords in the given file'''
        self.kwdb.add_file(filename)
        self._update_lib_tree()

    def _create_list(self, parent):
        listframe = ttk.Frame(parent, width=200, borderwidth=0)
        self.lib_tree = ttk.Treeview(listframe, selectmode="browse", columns=["id"], displaycolumns=[])
        self.lib_tree.heading("#0", text="Libraries", anchor="w")
        self.lib_tree_vsb = AutoScrollbar(listframe, orient="vertical", command=self.lib_tree.yview)
        self.lib_tree.configure(yscrollcommand=self.lib_tree_vsb.set)

        self.keyword_tree = ttk.Treeview(listframe, columns=["kw_id", "source","description"], 
                                 displaycolumns=["source", "description"])
        self.keyword_tree.column("source", width=120, stretch=False)
        self.keyword_tree.heading("#0", text="Keyword Name", anchor="w")
        self.keyword_tree.heading("source", text="Source", anchor="w")
        self.keyword_tree.heading("description", text="Description", anchor="w")
        self.keyword_tree_ysb = AutoScrollbar(listframe, orient="vertical", command=self.keyword_tree.yview)
        self.keyword_tree.configure(yscrollcommand=self.keyword_tree_ysb.set)

        self.lib_tree.grid(row=0, column=0, sticky="nsew")
        self.lib_tree_vsb.grid(row=0, column=1, sticky="ns")
        self.keyword_tree.grid(row=0, column=2, sticky="nsew")
        self.keyword_tree_ysb.grid(row=0, column=3, sticky="ns")
        listframe.grid_rowconfigure(0, weight=1)
        listframe.grid_columnconfigure(2, weight=1)
        return listframe
        
    def _update_lib_tree(self):
        children = self.lib_tree.get_children("")
        self.lib_tree.delete(*children)
        item = self.lib_tree.insert("", "end", text="All", values=[ALL_ID])
        self.lib_tree.selection_set((item,))
        maxwidth = 0
        for (collection_name, collection_id) in self.kwdb.get_collections():
            item = self.lib_tree.insert("", "end", text=collection_name, values=[collection_id])
            maxwidth = max(maxwidth, len(collection_name))

        # the +16 is for the space reserved for the image in the TreeView
        width = self.fonts.default.measure("M"*maxwidth) + 16
        self.lib_tree.column("#0", width=width)
        
    def _create_ui(self):
        self.filter = FilterBox(self)
        self.filter.bind("<<Search>>", self._on_search)
        self.filter.entry.bind("<Down>", self._on_down)
        self.filter.entry.bind("<Up>", self._on_up)

        pw = tk.PanedWindow(self, orient="vertical", borderwidth=0, 
                            background=self.colors.accent,
                            sashwidth=4, sashpad=0)
        listframe = self._create_list(pw)
        dataframe = self._create_data(pw)
        pw.add(listframe)
        pw.add(dataframe)

        self.filter.pack(side="top", fill="x", pady=2)
        pw.pack(side="top", fill="both", expand="true", padx=4, pady=4)
        
    def _create_data(self, parent):
        dataframe = ttk.Frame(parent, borderwidth=1, relief="sunken")

        self.text = CustomText(dataframe, wrap="word", borderwidth=0, width=120, 
                               font=self.fonts.default, highlightthickness=0)
        self.text_ysb = AutoScrollbar(dataframe, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=self.text_ysb.set)

        self.text.grid(row=0, column=0, sticky="nsew", padx=4)
        self.text_ysb.grid(row=0, column=1, sticky="ns")
        dataframe.grid_rowconfigure(0, weight=1)
        dataframe.grid_columnconfigure(0, weight=1)

        self.text.tag_configure("name", font=self.fonts.heading)
        self.text.tag_configure("args", font=self.fonts.italic)
        self.text.tag_configure("example", background="lightgray")
        self.text.tag_configure("search_string", background="yellow", 
                                borderwidth=1, relief="raised")

        return dataframe

    def _get_keywords(self, library, search_string,type):
        '''Return a list of all keywords that match the criteria'''
        keywords = []
        search_string = search_string.lower()
        
        for kw in self.kwdb.get_keywords():
            keywords.append(kw)
        return keywords

    def _on_lib_select(self, event):
        '''Callback for when user selects a library'''
        if not self.winfo_viewable(): return
        self.search()

    def _on_up(self, event):
        '''Callback for when user presses up arrow in search box'''
        if len(self.keyword_tree.selection()) == 0:
            return
        current = self.keyword_tree.selection()[0]
        prev_item = self.keyword_tree.prev(current)
        if prev_item:
            self.keyword_tree.selection_clear()
            self.keyword_tree.selection_set(prev_item)
            self.keyword_tree.see(prev_item)

    def _on_down(self, event):
        '''Callback for when user presses down arrow in search box'''
        if len(self.keyword_tree.selection()) == 0:
            return
        current = self.keyword_tree.selection()[0]
        next_item = self.keyword_tree.next(current)
        if next_item:
            self.keyword_tree.selection_clear()
            self.keyword_tree.selection_set(next_item)
            self.keyword_tree.see(next_item)

    def _on_visibility(self, event):
        '''Callback for when the UI is first realized'''
        # this causes the list to be updated with all the loaded files
        self.search()
        self.bind("<Visibility>", None)
        self.filter.set_focus()

    def _on_list_select(self, event):
        '''Callback for when user clicks on a keyword'''
        selection = self.keyword_tree.selection()
        item = selection[0]
        (kwid, library, description) = self.keyword_tree.item(item, "values")
        self.text.configure(state="normal")
        self.text.delete(1.0, "end")

        sql_result = self.kwdb.execute('''
            SELECT kw.name, kw.id, kw.doc, kw.args, c.name
            FROM keyword_table as kw
            JOIN collection_table as c
            WHERE kw.id == ?
        ''', (kwid,))
        (kw_name, kw_id, kw_doc, kw_args, collection_name) = sql_result.fetchone()

        self.text.insert("end", kw_name + "\n", "name", "\n")
        if len(kw_args) > 0:
            self.text.insert("end", "Arguments: %s\n\n" % kw_args, "args")
        self.text.insert("end", kw_doc)
        self.text.highlight_pattern("^\|.*?$", self._on_highlight_example)
        self.text.highlight_pattern("(?iq)"+self.filter.get_string(), 
                                    self._on_highlight_search_string)
        self.text.configure(state="disabled")

    def _on_highlight_search_string(self):
        '''Callback to apply highlighting of the search string'''
        self.text.tag_add("search_string", "matchStart", "matchEnd")

    def _on_highlight_example(self):
        '''Callback to apply highlighting on an example'''
        self.text.tag_add("example", "matchStart", "matchEnd+1c")

    def _on_search(self, *args):
        '''Callback for when user changes the search string'''
        self.search()

        
class FilterBox(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.search_type = tk.StringVar()
        self.search_string = tk.StringVar()
        self.search_type.set("both")
        self.label = ttk.Label(self, text="Search:")
        self.entry = SearchBox(self, textvariable=self.search_string, width=40)
        self.radio1 = ttk.Radiobutton(self, text="Name only", value="name", 
                                      variable=self.search_type)
        self.radio2 = ttk.Radiobutton(self, text="Name and Documentation", 
                                      value="both", variable=self.search_type)
        self.entry.pack(side="left", expand=False, padx=4)
        self.radio1.pack(side="left", padx=(0,8))
        self.radio2.pack(side="left", padx=(0,8))

        self.search_string.trace("w", self._on_search)
        self.search_type.trace("w", self._on_type)

    def set_focus(self):
        self.entry.focus()

    def _on_type(self, *args):
        self.event_generate("<<Search>>")

    def get_type(self):
        return self.search_type.get()

    def get_string(self):
        return self.search_string.get()

    def _on_search(self, *args):
        self.event_generate("<<Search>>")

class CustomText(tk.Text):
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)
        # N.B. giving the IntVar a unique name that begins with ::
        # makes it a global tcl variable which works around a bug
        # in tkinter
        self._countvar = tk.IntVar(master=self, name="::__count__")
        self.bind("<1>", lambda event: self.focus_set())

    def highlight_pattern(self, pattern, func, start="1.0", end="end"):
        '''Apply the given tag to all text that matches the given pattern'''

        start = self.index(start)
        end = self.index(end)
        self.mark_set("matchStart",start)
        self.mark_set("matchEnd",start)
        self.mark_set("searchLimit", end)

        while True:
            index = self.search(pattern, "matchEnd","searchLimit",
                                count=self._countvar, regexp=True)
            count = self._countvar.get()

            if index == "" or count == 0: break
            self.mark_set("matchStart", index)
            self.mark_set("matchEnd", "%s+%sc" % (index,count))
            func()

if __name__ == "__main__":
    import sys
    app = KeywordToolApp()
    app.mainloop()
