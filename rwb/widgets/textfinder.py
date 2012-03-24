'''TextFinder - a widget for searching through a text widget

'''

import Tkinter as tk
import ttk

class TextFinder(ttk.Frame):
    def __init__(self, parent, text_widget):
        self.text = text_widget
        ttk.Frame.__init__(self, parent)

        validatecommand = (self.register(self._on_validate), "%P")

        self._jobs = []
        self._stringvar = tk.StringVar()
        self._highlightvar = tk.IntVar()
        self._highlightvar.set(1)

        self.label = ttk.Label(self, text="Find:", anchor="e")
        self.sep = ttk.Separator(self, orient="horizontal")
        self.entry = ttk.Entry(self, textvariable=self._stringvar, exportselection=False, 
                          validate="key", validatecommand=validatecommand)
        self.next_button = ttk.Button(self, text="Find Next",
                                 style="Toolbutton", command=self._on_next)
        self.prev_button = ttk.Button(self, text="Find Previous",
                                 style="Toolbutton", command=self._on_previous)
        self.highlight_button = ttk.Checkbutton(self, text="Highlight",
                                           onvalue = 1, offvalue=0,
                                           variable=self._highlightvar,
                                           command=self._on_highlight)
        self.info_label = ttk.Label(self, anchor="e")
        self.hide_button = ttk.Button(self, text="[x]", 
                                      style="Toolbutton", command=self._on_cancel)

        self.sep.grid(row=0, column=0, columnspan=7,sticky="ew", pady=2)
        self.label.grid(row=1, column=0, sticky="e")
        self.entry.grid(row=1, column=1, sticky="ew")
        self.next_button.grid(row=1, column=2)
        self.prev_button.grid(row=1, column=3)
        self.highlight_button.grid(row=1, column=4)
        self.info_label.grid(row=1, column=5, sticky="nsew", padx=(0, 10))
        self.hide_button.grid(row=1, column=6)
        self.grid_columnconfigure(5, weight=1)

        self.entry.bind("<Return>", self._on_next)
        self.entry.bind("<Control-n>", self._on_next)
        self.entry.bind("<Control-p>", self._on_previous)
        self.entry.bind("<Control-g>", self._on_next)
        self.entry.bind("<Escape>", self._on_cancel)

        self.text.tag_configure("find", background="yellow", foreground="black")
        self.text.tag_configure("current_find", background="bisque")
        self.text.tag_raise("find")
        self.text.tag_raise("current_find", "find")
        self.text.tag_raise("current_find", "sel")
        self.text.tag_configure("current_find", 
                                background=self.text.tag_cget("sel", "background"),
                                foreground=self.text.tag_cget("sel", "foreground"))


    def begin(self, pattern, start="insert", direction="forwards"):
        '''Begin a new search'''
        self.reset()
        start = self.text.index(start)

        if direction == "forwards":
            range1 = (start, "end")
            if self.text.compare(start, "!=", "1.0"):
                range2 = ("1.0", start)
            else:
                range2 = ()
        else:
            range1 = (start, "1.0")
            if self.text.compare(start, "<", "end"):
                range2 = ("end", start)
            else:
                range2 = ()

        # tkinter's text widget doesn't support the -all option for searching,
        # so we'll have to directly interface with the tcl subsystem
        command = [self.text._w, "search", "-nocase", "-all"]
        if direction != "forwards":
            command.append("-backwards")
        command.append(pattern)

        # search first from start to EOF, then from 1.0 to 
        # the starting point. Why? Most likely the user is
        # wanting to find the next occurrance which is what
        # this algorithm results in.
        result1 = self.tk.call(tuple(command + ["insert linestart", "end"]))
        result2 = self.tk.call(tuple(command + ["1.0", "insert lineend"]))

        # why reverse result2? It represents results above the
        # starting point, so if result1 is null, this guarantees
        # that the first result is nearest the search start
        result = list(result1) + list(reversed(result2))
        if len(result) > 0:
            i = result[0]
            self._current_find(i, "%s + %sc" % (i, len(pattern)))
        for index in result:
            self.text.tag_add("find", index, "%s + %sc" % (index, len(pattern)))

    def reset(self):
        '''Reset the searching mechanism

        This will stop any pending jobs and remove the special tags
        '''
        self.info_label.configure(text="")
        for job in self._jobs:
            self.after_cancel(job)
        self._jobs = []
        self.text.tag_remove("current_find", 1.0, "end")
        self.text.tag_remove("find", 1.0, "end")
            
    def _current_find(self, start, end):
        self.text.tag_remove("current_find", 1.0, "end")
        self.text.tag_add("current_find", start, end)
        self.text.tag_remove("sel", 1.0, "end")
        self.text.tag_add("sel", start, end)
        self.text.mark_set("insert", start)
        self.text.see("insert")

    def next(self):
        search_range = self.text.tag_nextrange("find", "insert")
        # if the cursor is inside the range we just found, look a 
        # little further
        if (len(search_range) == 2 and
            self.text.compare("insert", "<=", search_range[1]) and
            self.text.compare("insert", ">=", search_range[0])):
            search_range = self.text.tag_nextrange("find", search_range[1])
            
        # if the range is null, wrap around to the start of the widget
        if len(search_range) == 0:
            search_range = self.text.tag_nextrange("find", 1.0)
            self.info_label.configure(text="find wrapped")
            self.bell()

        # if, after all that, the range is still null, well, blimey!
        if len(search_range) == 0:
            self.info_label.configure(text="pattern not found (3)")
            self.bell()
        else:
            self._current_find(*search_range)

    def previous(self):
        search_range = self.text.tag_prevrange("find", "insert")
        # if the cursor is inside the range we just found, look a 
        # little further
        if (len(search_range) == 2 and
            self.text.compare("insert", "<=", search_range[1]) and
            self.text.compare("insert", ">=", search_range[0])):
            search_range = self.text.tag_prevrange("find", search_range[0])
            
        # if the range is null, wrap around to the end of the widget
        if len(search_range) == 0:
            search_range = self.text.tag_prevrange("find", "end")
            self.info_label.configure(text="find wrapped")
            self.bell()

        # if, after all that, the range is still null, well, blimey!
        if len(search_range) == 0:
            self.info_label.configure(text="pattern not found (2)")
            self.bell()
        else:
            self._current_find(*search_range)

    def _on_cancel(self, event=None):
        self.reset()

    def _on_highlight(self, event=None):
        if self._highlightvar.get():
            self.text.tag_configure("find", background="yellow", foreground="black")
        else:
            self.text.tag_configure("find", background="", foreground="")

    def _on_previous(self, event=None):
        self.previous()

    def _on_next(self, event=None):
        self.next()

    def _on_validate(self, P):
        '''Called whenever the search string changes
        
        This method will cancel any existing search that
        is in progress, then start a new search if the passed
        in string is not empty

        This is called from the entry widget validation command, so 
        even though we're not validating anything per se, we still
        need to return True or this method will stop being called. 
        '''
        self.info_label.configure(text="")
        self.reset()
        if len(P) > 0:
            self.begin(P)
        return True


if __name__ == "__main__":
    root = tk.Tk()
    text = tk.Text(root)
    finder = TextFinder(root, text)
    text.pack(side="top", fill="both", expand=True)
    finder.pack(side="bottom", fill="x")
    text.insert("end",'''this is the first line
this is the second line
this is the third line''')
    text.mark_set("insert", 1.0)
    root.mainloop()
