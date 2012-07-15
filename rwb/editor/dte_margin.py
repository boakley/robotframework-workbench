'''A margin widget designed to augment the DynamicTableEditor

This displays line numbers and has some bindings for selecting whole rows

'''

import Tkinter as tk
import sys

class DteMargin(tk.Canvas):
    '''A widget to display line numbers and markers for a DynamicTableEditor widget'''
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.dte = None
        self.bind("<ButtonPress-1>", self._on_linenumber_click)
        self.bind("<Control-ButtonPress-1>", self._on_linenumber_control_click)
        self.bind("<Shift-ButtonPress-1>", self._on_linenumber_move)
        self.bind("<B1-Motion>", self._on_linenumber_move)
        
    def attach(self, dte):
        '''Attach to a dte widget'''
        self.dte = dte
        self.dte.margin = self
        padding = int(self.dte.cget("padx")) + int(self.cget("width"))
        self.dte.configure(padx=padding)
        self.place(x=-padding,y=0, relheight=1.0, in_=self.dte)
        self.dte.add_post_change_hook(lambda *args: self.refresh())

    def refresh(self):
        '''Refresh line numbers and markers'''
        self.update_linenumbers()
        self.update_markers()
        
    def _get_linenumber(self, index):
        return int(self.dte.index(index).split(".")[0])

    def update_markers(self, *args):
        '''This creates a marker which represents the current statement'''
        current_line = self.dte.index("insert").split(".")[0]
        start = self.dte.find_start_of_statement("insert")
        end = self.dte.find_end_of_statement("insert")
        self.set_marker(start, end)
            
    def set_marker(self, start, end):
        # start and end may be string indices, so we need to convert
        # them to integers
        start = int(float(start))
        end=int(float(end))
        bg = self.cget("background")
        self.itemconfigure("marker", outline=bg, fill=bg)
        for i in range(start, end+1):
            self.itemconfigure("marker-%s" %i, outline="blue", fill="blue")

    def update_linenumbers(self, *args):
        '''redraw line numbers for visible lines, and add invisible markers

        This may seem like a rather compute-intensive thing to
        do, but in practice it's pretty quick (on the order of
        5-8ms when there are 50 lines displayed, last time I
        measured)
        '''
        self.delete("all")
        window_height = self.winfo_height()
        window_width = self.winfo_width()
        first = int(self.dte.index("@0,0").split(".")[0])
        last = int(self.dte.index("@0,%s"%window_height).split(".")[0])
        self.create_line(0, 1, 0, window_height, fill="gray", tags=("border",))
        self.create_line(window_width-1, 1, window_width-1, window_height, fill="gray", tags=("border",))
        bg = self.dte.cget("background")
        markerx = window_width-3
        for i in range(first, last+1):
            dline= self.dte.dlineinfo("%s.0" % i)
            if dline is None: break
            y = dline[1]
            last_id = self.create_text(window_width-8,y,anchor="ne", text=str(i))
            self.create_rectangle(markerx, y, window_width-2, y+dline[3],
                                  outline=bg, fill=bg, tags=("marker", "marker-%s" % i))
            self.create_line(0,y-1, window_width+3, y-1, fill="gray")
        self.lift("border")

        # if the line numbers don't fit, adjust the size and try
        # again. Danger Will Robinson! We only do this if the window
        # is visible, otherwise we get into a nasty loop at startup.
        if self.winfo_viewable():
            bbox = self.bbox(last_id)
            required_width=bbox[2]-bbox[0]
            if bbox[0] < 0:
                self.configure(width=(window_width + abs(bbox[0]) + 4))
                self.after(1, self.update_linenumbers, False)

    def mark_current_statement(self):
        start = self.find_start_of_statement("insert")
        end = self.find_end_of_statement("insert")
        self.tag_remove("w00t", 1.0, "end")
        self.tag_add("w00t", start, "%s lineend+1c" % end)

    def _on_linenumber_control_click(self, event):
        text_index = self.dte.index("@%s,%s" % (event.x, event.y))
        self.dte.mark_set("click", "%s linestart" % text_index)
        self.dte.tag_add("sel", "%s linestart" % text_index, "%s lineend+1c" % text_index)
        self.dte.mark_set("insert", "%s linestart" % text_index)
        
    def _on_linenumber_click(self, event):
        try:
            text_index = self.dte.index("@%s,%s" % (event.x, event.y))
            self.dte.mark_set("click", "%s linestart" % text_index)
            self.dte.tag_remove("sel", "1.0", "end")
            self.dte.tag_add("sel", "%s linestart" % text_index, "%s lineend+1c" % text_index)
            self.dte.mark_set("insert", "%s lineend" % text_index)
        except Exception, e:
            import sys; sys.stdout.flush()

    def _on_linenumber_move(self, event):
        try:
            text_index = self.dte.index("@%s,%s" % (event.x, event.y))
            self.dte.tag_remove("sel", "1.0", "end") 
            if self.dte.compare(text_index, ">", "click"):
                self.dte.tag_add("sel", "click", "%s lineend+1c" % text_index)
            else:
                self.dte.tag_add("sel", "%s linestart" % text_index, "click lineend+1c")
            self.dte.mark_set("insert", "%s lineend" % text_index)
        except Exception, e:
            pass

