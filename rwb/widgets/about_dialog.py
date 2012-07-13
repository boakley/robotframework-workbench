'''AboutDialog - a simple About box'''

import Tkinter as tk
import rwb

class AboutBoxDialog(tk.Toplevel):

    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)

        self.text = tk.Text(self, wrap="word", highlightthickness=0, 
                            width=60, height=20, 
                            borderwidth=2, relief="groove",
                            background=self.cget("background"),
                            padx=10, pady=10)
        self.text.pack(side="top", fill="both", expand=True, padx=12, pady=12)
        self.text.tag_configure("center", justify="center")
        self.text.tag_configure("heading", foreground="#b22222")
        self.text.tag_configure("link", foreground="blue", underline=True)
        self.text.tag_bind("link", "<Enter>", self._on_link_enter)
        self.text.tag_bind("link", "<Leave>", self._on_link_leave)
        self.text.tag_bind("link", "<1>", self._on_link_click)

        self._add_info()
        self.buttonbox = tk.Frame(self)
        self.buttonbox.pack(side="bottom", fill="x", padx=4,pady=4)
        ok_button = tk.Button(self.buttonbox, text="OK", width=10, 
                              command=self.ok, default="active")
        ok_button.pack(side="top", expand=True)
        self.bind("<Return>", self.ok)

    def show(self):
        self.wm_deiconify()

    def ok(self):
        self.destroy()

    def _add_info(self):
        self.text.configure(state="normal")

        self.text.insert("end", "\nRobot Framework Workbench\nVersion %s\n\n" % rwb.__version__, ("center", "heading"))

        self.text.insert("end", "This application uses icons from the Silk " +
                         "icon set created by Mark James, which is provided " +
                         "under the Creative Commons 2.5 license. For more " +
                         " information see ")
        self.text.insert("end", "http://www.famfamfam.com/lab/icons/silk/", ("link",))
        self.text.insert("end", "\n\n")

        self.text.insert("end", "This application uses the ConfigObj module " +
                         "written by Michael Foord and Nicola Larosa, which " +
                         "is provided under a BSD license. For more information " +
                         "see ")
        self.text.insert("end", "http://www.voidspace.org.uk/python/configobj.html", ("link",))
        self.text.insert("end", "\n\n")

        self.text.insert("end", "For more information on the robotframework workbench see ")
        self.text.insert("end", "https://github.com/boakley/robotframework-workbench/wiki", ("link",))
        self.text.configure(state="disabled")

    def _on_link_click(self, event):
        index = self.text.index("@%s,%s" % (event.x, event.y))
        ranges = self.text.tag_ranges("link")
        for i in range(0, len(ranges), 2):
            start,end = ranges[i], ranges[i+1]
            if (self.text.compare(start, "<=", index) and
                self.text.compare(index, "<=", end)):
                url = self.text.get(start, end)
                try:
                    import webbrowser
                    webbrowser.open(url)
                except Exception, e:
                    print "error opening web browser:", e

    def _on_link_enter(self, event):
        self.text.configure(cursor="left_ptr")

    def _on_link_leave(self, event):
        self.text.configure(cursor="xterm")
        
