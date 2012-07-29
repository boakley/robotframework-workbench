import Tkinter as tk
import colorsys
import ttk

# these colors assume a grayish background. Good Enough for now.
COLORS = ("#000000", "#111111","#222222","#333333",
          "#444444", "#555555","#666666","#777777",
          "#888888", "#999999","#AAAAAA","#BBBBBB")

class Statusbar(tk.Frame):
    '''A statusbar widget'''
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.bg = self.winfo_toplevel().cget("background")
        self.configure(background=self.bg)
        sep = ttk.Separator(self, orient="horizontal")
        sep.pack(side="top", fill="x", padx=4)
        grip = ttk.Sizegrip(self)
        grip.pack(side="right")
        # Why a canvas? I guess I'm trying to be clever and support
        # text that fades away instead of blinking away. 
        self.canvas = self.CustomCanvas(self, borderwidth=0, highlightthickness=0,
                                        background=self.bg)
        self.canvas.pack(side="left", fill="both", expand=True, padx=(4,0))
        self.canvas.create_text((0,0), text="X")
        bbox = self.canvas.bbox("all")
        (x0,y0,x1,y1) = bbox if bbox is not None else (0,0,0,0)
        self.canvas.delete("all")
        border=2
        height = (y1-y0) + (2*border)
        self.canvas.configure(height=height)
        self.messages = []
        self.section = {}

    def add_progress(self, mode="indeterminate"):
        self.progress_bar = ttk.Progressbar(self, mode=mode)
        self.progress_bar.pack(side="right")
        separator = tk.Frame(self, borderwidth=2, relief="groove", width=2)
        separator.pack(side="right", fill="y", padx=4, pady=4)

    def progress_start(self):
        self.progress_bar.start()

    def progress_stop(self):
        self.progress_bar.stop()

    def add_section(self, name, width, string=None):
        '''Define a new section in the statusbar
        
        This section will be added to the right of the main message
        aread but to the left of any other sections.
        '''
        self.section[name] = tk.StringVar()
        if string is not None:
            self.section[name].set(string)
        l = tk.Label(self, textvariable=self.section[name], width=width, background=self.bg)
#        s = ttk.Separator(self, orient="vertical")
        s = tk.Frame(self, borderwidth=2, relief="groove", width=2)
        l.pack(side="right")
        s.pack(side="right", fill="y", padx=4, pady=4)

    def get(self, section_name):
        return self.section[section_name].get()

    def set(self, section_name, string):
        '''Displays a string in one of the statusbar sections

        The string that is displayed is static; it will not fade
        like the main area of the statusbar.
        '''
        self.section[section_name].set(string)

    def fit(self):
        '''Fit the strings in the canvas

        Move everything right until it is all in the viewable area
        '''
        bbox = self.canvas.bbox("all")
        deltax = abs(bbox[0] - 4)
        self.canvas.move("all", deltax, 0)
        
    def message(self, string, lifespan=5000, clear=False):
        '''Display a message in the statusbar

        This message will fade out after the given lifespan. If there
        is already a message being displayed it will be moved to the
        right to make room for the new message.
        '''
        if clear:
            self.canvas.delete("all")
        # if there's already an existing message, we want to add
        # a separator to it. First, let's prune any old messages
        # from our stack
        self.messages = [m for m in self.messages if m.canvas_id is not None]
        if len(self.messages) > 0:
            self.messages[0].add_separator()
        self.messages.insert(0,self.Message(self, string, lifespan=lifespan))

    class CustomCanvas(tk.Canvas):
        def fit(self):
            '''Makes sure nothing overlaps the left edge'''
            bbox = self.bbox("all")
            if bbox is not None and len(bbox) > 0:
                deltax = abs(bbox[0] - 4)
                self.move("all", deltax, 0)
            
    class Message(object):
        '''A text string that fades away over time. 

        Silly, but why not? A little eye candy never hurt.
        '''
        def __init__(self, statusbar, string, lifespan=5000):
            self.statusbar = statusbar
            self.canvas = statusbar.canvas
            self.color_index = 0
            self.canvas_id = self.canvas.create_text((0,2), anchor="ne", text=string.strip(),
                                                fill=COLORS[self.color_index])
            self._has_separator = False
            self.canvas.fit()
            if lifespan > 0:
                self.canvas.after(lifespan, self.decay)

        def add_separator(self):
            '''Add a separator to the left of the text string'''
            if not self._has_separator:
                text = u"\u25B8 %s" % self.canvas.itemcget(self.canvas_id, "text")
                self.canvas.itemconfigure(self.canvas_id, text=text)
                self.canvas.fit()
                self._has_separator = True

        def decay(self):
            '''Slowly fade out the message'''
            self.color_index += 1
            if self.color_index >= len(COLORS):
                self.canvas.delete(self.canvas_id)
                self.canvas_id = None
            else:
                self.canvas.itemconfigure(self.canvas_id, fill=COLORS[self.color_index])
                self.canvas.after(100, self.decay)

if __name__ == "__main__":
    app = SampleApp()
    app.mainloop()


