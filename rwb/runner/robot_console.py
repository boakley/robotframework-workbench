import Tkinter as tk
import ttk
import re

class RobotConsole(tk.Frame):
    '''This class presents a scrollable text widget to display test stdout'''
    controller = None

    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.text = tk.Text(self, width=80, borderwidth=0, highlightthickness=0, wrap=None)
        vsb = AutoScrollbar(self, command=self.text.yview, orient="vertical")
        hsb = AutoScrollbar(self, command=self.text.xview, orient="horizontal")
        self.text.configure(xscrollcommand=hsb.set,yscrollcommand=vsb.set)
        self.text.tag_configure("stderr", foreground="#b22222")
        self.text.tag_configure("debug", foreground="gray", elide=False)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.text.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _replace_ansi_colors(self, start, end):
        '''Replace ANSI color escape sequnces

        Presently this only supports foreground colors, which is all that
        robot currently uses.
        '''
        count = tk.IntVar()
        pattern = "\x1b\[(3[0-7, 9])m(.*?)\x1b\[0?m"
        search_result=self.text.search(pattern, start, regexp=True, count=count)
        text_color = {"30": "black",  "31": "red", "32": "green", 
                      "33": "yellow", "34": "blue", "35": "magenta",
                      "36": "cyan",   "37": "white", "39": "black"}
        for color in ("black","red","green","yellow","blue",
                      "magenta", "cyan","white","black"):
            self.text.tag_configure("ansi-fg-%s" % color, foreground=color)
            
        if search_result:
            print "*BOOM*"
            s = self.text.get(foo, "%s + %sc" % (foo, count.get()))
            match = re.match(pattern, s)
            if match:
                s = match.group(2)
                # should always be true, since we're using the same pattern...
                tag = "ansi-fg-%s" % text_color[match.group(1)]
                text = match.group(2)
 #               self.text.tag_configure(tag, foreground=text_color[match.group(1)])
                self.text.delete(foo, "%s+%sc" % (foo, count.get()))
                self.text.insert(foo, text, tag) 
        
    def reset(self):
        self.text.delete(1.0, "end")

    def append(self, text, *tags):
        self.text.mark_set("last", "end-1c")
        self.text.mark_gravity("last", "left")
        self.text.insert("end", text, tags)
        self._replace_ansi_colors("last", "end")

    def clear(self, text):
        self.text.delete("1.0", "end")

class AutoScrollbar(ttk.Scrollbar):
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter...
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        ttk.Scrollbar.set(self, lo, hi)
