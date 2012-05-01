import Tkinter as tk
import ttk

class BottomTabNotebook(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.tabs = {}
        self._tab_order = []
        self.canvas = tk.Canvas(self, background=self.winfo_toplevel().cget("background"), 
                                height=200, borderwidth=0,
                                highlightthickness=0)
        self.canvas.pack(side="bottom", fill="x", padx=4)
        self.container = tk.Frame(self, width=800, height=400, borderwidth=1, relief="sunken")
        self.container.pack(side="right", fill="both", expand=True)
        self._current = None
        self._redraw_job = None
        self.canvas.bind("<Configure>", self._on_configure)

    def add(self, widget, text=None):
        '''Add a new tab'''
        tab = NotebookTab(self, text, widget)
        self._tab_order.append(tab)
        x = 4 if len(self._tab_order) == 1 else self._tab_order[-2].x1 + 8
        self.canvas.coords(tab.text_object, (x,4))
        bbox = self.canvas.bbox("all")
        height = bbox[3] + 2
        self.canvas.configure(height=height)
        self.tabs[text] = tab
        self.redraw(text)

    def redraw(self, name=None):
        '''Redraw all of the tabs'''
        self._current = name
        for tab in self._tab_order:
            current = (tab.name == name)
            tab.redraw(current)
            tab.widget.place_forget()
        try:
            self.canvas.tag_raise("current", "others")
        except:
            pass
        self.canvas.tag_raise("text")
        self.tabs[name].widget.place(in_=self.container, x=4, y=0, relwidth=1, relheight=1)
        self.tabs[name].widget.lift()

    def _on_configure(self, event):
        '''Redraw the tabs when the canvas changes size'''
        if self._redraw_job is not None:
            self.after_cancel(self._redraw_job)
        self._redraw_job = self.after(500, self.redraw, self._current)

class NotebookTab(object):
    def __init__(self, notebook, name, widget):
        self._canvas = notebook.canvas
        self._notebook = notebook
        self.name = name
        self.widget=widget
        label = "%-10s" % name
        self.text_object = \
            self._canvas.create_text(4,0, text=label, 
                                     tags=(name, "text"), anchor="nw")
        self.tab_object = \
            self._canvas.create_polygon(0,0,1,1, tags=(name, "tab"), outline="black")
        self._canvas.tag_bind(name, "<1>", self._on_click)

    def _on_click(self, event):
        self._notebook.redraw(self.name)

    @property
    def x0(self):
        '''Return X coordinate of upper-left corner of text box'''
        return self._canvas.bbox(self.text_object)[0]
    @property
    def x1(self):
        '''Return X coordinate of lower-right corner of text box'''
        return self._canvas.bbox(self.text_object)[2]

    def redraw(self, current=False):
        '''Redraw the tab'''
        canvas_width = self._canvas.winfo_width()
        (x0,y0,x1,y1) = self._canvas.bbox(self.text_object)
        height = y1-y0
        x0 = max(x0 - 8, 0)
        y0 = y0 - 1
        x1 = max(x1 - 8, 0)
        y1 = y1 + 2
        x2 = x1 + height
        if current:
            y1 = y1 + 1
            color = "white"
            coords = (0,0, 0,y0, x0,y0, x0,y1, x1,y1, 
                       x2,y0, canvas_width,y0, canvas_width,0)
            tags = (self.name,"current")
        else:
            color = "lightblue"
            coords = (x0,y0, x0,y1, x1, y1, x2,y0)
            tags = (self.name,"others")

        self._canvas.coords(self.tab_object, coords)
        self._canvas.itemconfigure(self.tab_object, fill=color, tags=tags)
        self._canvas.tag_raise("current")
