import Tkinter as tk
import ttk
from rwb.images import data as icons
import tkFont

class RobotLogMessages(ttk.Frame):
    '''Provides a list of messages produced by a running test'''
    def __init__(self, *args, **kwargs):
        ttk.Frame.__init__(self, *args, **kwargs)

        self._show_level = {
            "TRACE": tk.BooleanVar(self, value=False),
            "DEBUG": tk.BooleanVar(self, value=True),
            "INFO" : tk.BooleanVar(self, value=True),
            "WARN" : tk.BooleanVar(self, value=True),
            "ERROR": tk.BooleanVar(self, value=True),
            "PASS" : tk.BooleanVar(self, value=True),
            "FAIL" : tk.BooleanVar(self, value=True),
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

    def listen(self, event_id, event_name, args):
        if event_name == "log_message":
            attrs = args[0]
            time = attrs["timestamp"].split(" ")[1]
            data = (attrs["level"], time, attrs["message"], event_id)
            self._cache.append(data)
            self._add_tree_item(data)

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
            # FIXME: should only be doing this if the user
            # hasn't scrolled up...
            self.tree.see(node)

    
class RobotLogTree(tk.Frame):
    '''Provides a tree view for suite, test and keyword results'''
    def __init__(self, parent, *args, **kwargs):
        self._init_images()
        tk.Frame.__init__(self, *args, **kwargs)
        self.tree = ttk.Treeview(self, columns=("event_id", "timestamp"),
                                 displaycolumns=("timestamp",))
        self.tree.column("#0", stretch=True)
        tswidth = tkFont.nametofont("TkDefaultFont").measure("00:00:00.000")
        self.tree.column("timestamp", width=tswidth+8, stretch=False)
        self.tree.heading("event_id", text="event_id")
        self.tree.heading("timestamp", text="timestamp")
        vsb = ttk.Scrollbar(self, command=self.tree.yview, orient="vertical")
        hsb = ttk.Scrollbar(self, command=self.tree.xview, orient="horizontal")
        self.tree.configure(xscrollcommand=hsb.set, yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tree.tag_configure("FAIL", foreground="#b22222")
        self.tree.tag_configure("PASS", foreground="#009900")
        self.tree.tag_configure("WARN", foreground="#663300")
        self._controller = None
        self._nodes = [""]
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def reset(self):
        '''Remove all items from the view'''
        self._nodes = [""]
        for item in self.tree.get_children(""):
            self.tree.delete(item)

    def listen(self, event_id, name, args):

        dispatch = {
            "start_suite":   self._start_suite,
            "end_suite":     self._end_suite,
            "start_test":    self._start_test,
            "end_test":      self._end_test,
            "start_keyword": self._start_keyword,
            "end_keyword":   self._end_keyword,
            "log_message":   self._log_message,
            }

        if name in dispatch:
            dispatch[name](event_id, *args)

    def _init_images(self):
        self._image = {
            "suite": tk.PhotoImage(data=icons["table_multiple"]),
            "test":  tk.PhotoImage(data=icons["table"]),
            "keyword": tk.PhotoImage(data=icons["cog"]),
            }

    def _on_select(self, event=None):
        item=self.tree.selection()[0]
        self.event_generate("<<EventSelected>>")

    # the following methods accept the same arguments as traditional robot
    # listeners, except there's an additional first argument that is a 
    # unique id for this event (useful to associate objects in one listener
    # to objects in another listener)
    def _start_suite(self, event_id, name, attrs):
        parent = self._nodes[-1]
        starttime = attrs["starttime"].split(" ")[1]
        node = self.tree.insert(parent, "end", text=" %s" % name, 
                                open=True, image=self._image["suite"],
                                values=(event_id, starttime))
        self._nodes.append(node)

    def _end_suite(self, event_id, name, attrs):
        node = self._nodes.pop()

    def _start_test(self, event_id, name, attrs):
        parent = self._nodes[-1]
        node = self.tree.insert(parent, "end", text=" %s" % name, 
                                open=False,image=self._image["test"])
        self._nodes.append(node)

    def _end_test(self, event_id, name, attrs):
        node = self._nodes.pop()
        self.tree.item(node, tags=(attrs["status"]))

    def _start_keyword(self, event_id, name, attrs):
        parent = self._nodes[-1]
        string = " %s" % (" | ".join([name] + attrs["args"]))
        node = self.tree.insert(parent, "end", text=string, 
                                open=False,image=self._image["keyword"])
        self._nodes.append(node)

    def _end_keyword(self, event_id, name, attrs):
        node = self._nodes.pop()
        if attrs["status"] == "FAIL":
            self.tree.item(node, tags=("FAIL"))
            while node != "":
                parent = self.tree.parent(node)
                self.tree.item(parent, open=True)
                node = parent
        else:
            self.tree.item(node, tags=("PASS"))

    def _log_message(self, event_id, attrs):
        parent = self._nodes[-1]
        if attrs["level"] in ("INFO","WARN","ERROR"):
            string = "%s: %s" % (attrs["level"], attrs["message"].replace("\n", "\\n"))
            node = self.tree.insert(parent, "end", text=string, open=False)
