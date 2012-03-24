'''A margin widget designed to augment the DynamicTableEditor

This displays line numbers and has some bindings for selecting whole rows
'''

import Tkinter as tk
import sys

class DteMargin(tk.Canvas):
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.text = None
        self.bind("<ButtonPress-1>", self._on_linenumber_click)
        self.bind("<Control-ButtonPress-1>", self._on_linenumber_control_click)
        self.bind("<Shift-ButtonPress-1>", self._on_linenumber_move)
        self.bind("<B1-Motion>", self._on_linenumber_move)
        self.first = self.last = None
        
    def attach(self, text):
        self.text = text
        self.text.add_post_change_hook(self.update_markers)

    def _get_linenumber(self, index):
        return int(self.text.index(index).split(".")[0])

    def update_markers(self, *args):
        current_line = self.text.index("insert").split(".")[0]
        like_lines = self.text.find_like_rows(current_line)
        bg = self.cget("background")
        self.itemconfigure("marker", outline=bg, fill=bg)
        for i in like_lines:
            self.itemconfigure("marker-%s" % i, outline="blue", fill="blue")
            
    def update_linenumbers(self, *args):
        '''redraw line numbers for visible lines

        This may seem like a rather compute-intensive thing to
        do, but in practice it's pretty quick (on the order of
        5-8ms when there are 50 lines displayed, last time I
        measured)
        '''
        self.delete("all")
        window_height = self.winfo_height()
        window_width = self.winfo_width()
        first = int(self.text.index("@0,0").split(".")[0])
        last = int(self.text.index("@0,%s"%window_height).split(".")[0])
        self.create_line(0, 1, 0, window_height, fill="gray", tags=("border",))
        self.create_line(window_width-1, 1, window_width-1, window_height, fill="gray", tags=("border",))
        bg = self.text.cget("background")
        markerx = window_width-3
        for i in range(first, last+1):
            dline= self.text.dlineinfo("%s.0" % i)
            if dline is None: break
            y = dline[1]
            last_id = self.create_text(window_width-8,y,anchor="ne", text=str(i))
            self.create_rectangle(markerx, y, window_width-2, y+dline[3],
                                  outline=bg, fill=bg, tags=("marker", "marker-%s" % i))
            self.create_line(0,y-1, window_width+3, y-1, fill="gray")
        self.lift("border")
        self.update_markers()

        # if the line numbers don't fit, adjust the size
        # and try again. Danger Will Robinson! We only do
        # this if the window is visible, otherwise we get
        # into a nasty loop at startup.
        if self.winfo_viewable():
            bbox = self.bbox(last_id)
            required_width=bbox[2]-bbox[0]
            if bbox[0] < 0 and self.winfo_viewable():
                self.configure(width=(window_width + abs(bbox[0]) + 4))
                self.after(1, self.update_linenumbers, False)
            else:
                self.first = first
                self.last = last

    def _on_linenumber_control_click(self, event):
        text_index = self.text.index("@%s,%s" % (event.x, event.y))
        self.text.mark_set("click", "%s linestart" % text_index)
        self.text.tag_add("sel", "%s linestart" % text_index, "%s lineend+1c" % text_index)
        self.text.mark_set("insert", "%s linestart" % text_index)
        
    def _on_linenumber_click(self, event):
        try:
            text_index = self.text.index("@%s,%s" % (event.x, event.y))
            self.text.mark_set("click", "%s linestart" % text_index)
            self.text.tag_remove("sel", "1.0", "end")
            self.text.tag_add("sel", "%s linestart" % text_index, "%s lineend+1c" % text_index)
            self.text.mark_set("insert", "%s lineend" % text_index)
        except Exception, e:
            print "drat:", e
            import sys; sys.stdout.flush()

    def _on_linenumber_move(self, event):
        try:
            text_index = self.text.index("@%s,%s" % (event.x, event.y))
            self.text.tag_remove("sel", "1.0", "end") 
            if self.text.compare(text_index, ">", "click"):
                self.text.tag_add("sel", "click", "%s lineend+1c" % text_index)
            else:
                self.text.tag_add("sel", "%s linestart" % text_index, "click lineend+1c")
            self.text.mark_set("insert", "%s lineend" % text_index)
        except Exception, e:
            print "drat:", e

