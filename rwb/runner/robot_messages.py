import Tkinter as tk
import ttk
from rwb.widgets import AutoScrollbar

class RobotMessages(ttk.Frame):
    def __init__(self, *args, **kwargs):
        ttk.Frame.__init__(self, *args, **kwargs)

        self._show_level = {
            "TRACE": tk.BooleanVar(self, value=False),
            "DEBUG": tk.BooleanVar(self, value=True),
            "INFO":  tk.BooleanVar(self, value=True),
            "WARN":  tk.BooleanVar(self, value=True),
            "ERROR": tk.BooleanVar(self, value=True),
            "PASS":  tk.BooleanVar(self, value=True),
            "FAIL":  tk.BooleanVar(self, value=True),
            }

        option_frame = ttk.Frame(self)
        ttk.Label(option_frame, text="Show messages of type:").pack(side="left", padx=(0,8))
        for level in ("INFO", "WARN", "ERROR", "DEBUG", "TRACE"):
            cb = ttk.Checkbutton(option_frame, 
                                 text=level, 
                                 variable=self._show_level[level],
                                 onvalue=True, 
                                 offvalue=False,
                                 command=self.refresh)
            cb.pack(side="left", padx=(0,8))

        self.tree = ttk.Treeview(self, columns=("level", "time", "message"),
                                 displaycolumns=("level", "time", "message"),
                                 show=("headings",))
        self.tree.heading("level", text="Level")
        self.tree.heading("time", text="Time")
        self.tree.heading("message", text="Message")
        self.tree.column("level", width=100, stretch=False)
        self.tree.column("time", width=100, stretch=False)
        self.tree.column("message", stretch=True)
        vsb = ttk.Scrollbar(self, command=self.tree.yview, orient="vertical")
        hsb = ttk.Scrollbar(self, command=self.tree.xview, orient="horizontal")
        self.tree.configure(xscrollcommand=hsb.set, yscrollcommand=vsb.set)
        self.tree.tag_configure("DEBUG", foreground="gray")
        self.tree.tag_configure("TRACE", foreground="gray")
        self.tree.tag_configure("ERROR", background="#FF7e80")
        self.tree.tag_configure("FAIL", foreground="#b22222")
        self.tree.tag_configure("PASS", foreground="#009900")
        self.tree.tag_configure("WARN", background="#ffff00")
        self._cache = []

        option_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=4)
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def reset(self):
        self._cache = []
        for item in self.tree.get_children(""):
            self.tree.delete(item)

    def refresh(self):
        '''Refresh the view by deleting and re-adding all the items

        Sadly the treeview can't hide items, so to make something hidden
        I have to delete it.
        '''
        for item in self.tree.get_children(""):
            self.tree.delete(item)
        for data in self._cache:
            self._add_tree_item(data)

    def _add_tree_item(self, data):
        level, timestamp, message, event_id = data
        tags = (level,)
        strings = message.split("\n")
        if self._show_level[level].get():
            node = self.tree.insert("", "end", 
                                    values=(level, timestamp, strings[0],),
                                    open=False,
                                    tags=tags)
            for string in strings[1:]:
                node = self.tree.insert("", "end", 
                                        values=("", "", string),
                                        open=False,
                                        tags=tags)
            self.tree.see(node)

    def add(self, event_id, attrs):
        '''Add an item to the log'''
        time = attrs["timestamp"].split(" ")[1]
        data = (attrs["level"], time, attrs["message"], event_id)
        self._cache.append(data)
        self._add_tree_item(data)

