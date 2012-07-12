import Tkinter as tk
import ttk
from rwb.widgets import ToolButton
from rwb.images import data as icons

class CollapsibleFrame(ttk.Frame):
    def __init__(self, parent, title=">>>"):
        ttk.Frame.__init__(self, parent)
        self.trigger = ToolButton(self,
                                  text=title,
                                  width=0,
                                  tooltip="show command window",
                                  command=self.toggle)
        self.trigger.grid(row=0, column=0, sticky="nw")
        self.text = tk.Text(self, wrap="word", height=2, borderwidth=1, relief="solid")
        self.text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=4)
        self.grid_columnconfigure(1, weight=1)
        self.show(True)

    def toggle(self, event=None):
        self.show(not self.text.winfo_viewable())

    def show(self, show=True):
        if show:
            self.text.grid()
        else:
            self.text.grid_remove()

    def set(self, s):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", s)

    def get(self):
        self.text.get("1.0", "end-1c")
