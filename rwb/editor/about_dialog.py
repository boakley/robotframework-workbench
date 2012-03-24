'''AboutDialog - a simple About box'''

import Tkinter as tk

class AboutBoxDialog(tk.Toplevel):

    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)

        self.text = tk.Text(self, wrap="word", highlightthickness=0, 
                            width=60, height=20, 
                            background=self.cget("background"))
        self.text.pack(side="top", fill="both", expand=True, padx=8)
        self._add_info()
        self.buttonbox = tk.Frame(self)
        self.buttonbox.pack(side="bottom", fill="x", padx=4,pady=4)
        ok_button = tk.Button(self.buttonbox, text="OK", width=10, 
                              command=self.ok, default="active")
        ok_button.pack(side="top", expand=True)
        self.bind("<Return>", self.ok)

    def ok(self):
        self.destroy()

    def _add_info(self):
        self.text.tag_configure("center", justify="center")
        self.text.tag_configure("heading", foreground="#b22222")
        self.text.insert("end", "\nRobot Framework Workbench\n\n", ("center", "heading"))

        self.text.insert("end", "This application uses icons from the Silk " +
                         "icon set created by Mark James, which is provided " +
                         "under the Creative Commons 2.5 license. For more " +
                         " information see http://www.famfamfam.com/lab/icons/silk/\n\n")

        self.text.insert("end", "This application uses the ConfigObj module " +
                         "written by Michael Foord and Nicola Larosa, which " +
                         "is provided under a BSD license. For more information " +
                         "see http://www.voidspace.org.uk/python/configobj.html\n\n")
