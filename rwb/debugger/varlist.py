import Tkinter as tk
import ttk

'''
TODO: add ability to click on a value and change its value
Also, we can compute the width of the widest variable, and set
the column width to that dynamically.
'''

class VariableList(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.sb = ttk.Scrollbar(self, orient="vertical")
        self.varlist = ttk.Treeview(self, columns=("name","value"), 
                                    yscrollcommand=self.sb.set,
                                    show=("headings",))
        self.sb.configure(command=self.varlist.yview)
        self.sb.pack(side="right", fill="y")
        self.varlist.pack(side="left", fill="both", expand=True)
        self.varlist.heading("name", text="Variable name")
        self.varlist.heading("value", text="Variable value")
        self.varlist.column("name", width=200, stretch=False)
        self.varlist.column("value", stretch=True)

    def reset(self):
        for item in self.varlist.get_children(""):
            self.varlist.delete(item)

    def add(self, name, value):
        self.varlist.insert("", "end", values=(name, value,))

