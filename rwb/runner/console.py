import Tkinter as tk
import ttk
import re
import logging

class RobotConsole(tk.Frame):
    '''This class presents a scrollable text widget to display stdout/stderr'''
    controller = None

    def __init__(self, parent, background="white"):
        tk.Frame.__init__(self, parent, name="log_console", borderwidth=1, relief="sunken")
        self.text = tk.Text(self, width=80, borderwidth=0, highlightthickness=0, 
                            wrap="none", background=self.cget("background"),
                            font="TkFixedFont")
        vsb = ttk.Scrollbar(self, command=self.text.yview, orient="vertical")
        hsb = ttk.Scrollbar(self, command=self.text.xview, orient="horizontal")
        self.text.configure(xscrollcommand=hsb.set,yscrollcommand=vsb.set)
        self.text.tag_configure("stderr", foreground="#b22222")
        self.text.tag_configure("debug", foreground="gray", elide=False)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.text.grid(row=0, column=0, sticky="nsew", padx=(8,2), pady=4)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._controller = None

    def get_width(self):
        '''Return the width in characters of the console window'''
        # this is obviously incorrect, but close enough for now
        width = self.text.winfo_width()
        return width / 12

    def reset(self):
        '''Erases the data in the text widget'''
        self.text.delete(1.0, "end")

    def listen(self, id_, name, args):
        '''Listen for and respond to events from the test controller'''
        self.text.mark_set("last", "end-1c")
        self.text.mark_gravity("last", "left")
        should_autoscroll = (self.text.bbox("end-1c") is not None)
        try:
            if name in ("stdout", "stderr",):
                self.text.insert("end", args[0], name)
                self._replace_ansi_colors("last", "end")
        except Exception, e:
            logging.warn("error in listener: " + str(e))
        if should_autoscroll:
            self.text.update_idletasks()
            self.text.see("end")

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
            s = self.text.get(foo, "%s + %sc" % (foo, count.get()))
            match = re.match(pattern, s)
            if match:
                s = match.group(2)
                tag = "ansi-fg-%s" % text_color[match.group(1)]
                text = match.group(2)
                self.text.delete(foo, "%s+%sc" % (foo, count.get()))
                self.text.insert(foo, text, tag) 
        
