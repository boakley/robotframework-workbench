import sys
import os
import Tkinter as tk
import ttk
from rwb.lib import AbstractRwbApp
from rwb.widgets import Statusbar, ToolButton
from rwb.lib.configobj import ConfigObj
from logviewer import LogTree
import tkFileDialog


NAME="logviewer"

DEFAULT_SETTINGS = {
    NAME: {}
}

class LogViewerApp(AbstractRwbApp):
    def __init__(self):
        AbstractRwbApp.__init__(self, NAME, DEFAULT_SETTINGS)
        
        self._create_menubar()
        self._create_toolbar()
        self._create_statusbar()

        vsb = ttk.Scrollbar(self, orient="vertical")
        self.viewer = LogTree(self)
        vsb.configure(command=self.viewer.tree.yview)
        self.viewer.tree.configure(yscrollcommand=vsb.set)
        self.toolbar.pack(side="top", fill="x")
        self.statusbar.pack(side="bottom", fill="x")
        vsb.pack(side="right", fill="y")
        self.viewer.pack(side="top", fill="both", expand=True)

    def _create_toolbar(self):
        self.toolbar = ttk.Frame(self)
        suite_button = ToolButton(self.toolbar, text="Suites", width=0,
                                  tooltip="Expand to show all suites")
        test_button = ToolButton(self.toolbar, text="Test Cases",  width=0,
                                 tooltip="Expand to show all suites and test cases")
        kw_button = ToolButton(self.toolbar, text="Test Keywords",  width=0,
                               tooltip="Expand to show all suites, test cases, and their keywords")
        all_button = ToolButton(self.toolbar, text="All Keywords", width=0,
                                tooltip="Expand to show all suites, test cases, and keywords")
        suite_button.pack(side="left")
        test_button.pack(side="left")
        kw_button.pack(side="left")
        all_button.pack(side="left")

    def _create_menubar(self):
        self.menubar = tk.Menu(self)
        self.configure(menu=self.menubar)
        self.file_menu = tk.Menu(self.menubar, tearoff=False)
        self.file_menu.add_command(label="Open...", command=self._on_open)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self._on_exit)

        self.view_menu = tk.Menu(self.menubar, tearoff=False)
        self.view_menu.add_command(label="Expand Suites", underline=7)
        self.view_menu.add_command(label="Expand Test Cases", underline=7)
        self.view_menu.add_command(label="Expand Test Case Keywords", underline=17)
        self.view_menu.add_command(label="All Keywords", underline=0)

        self.menubar.add_cascade(menu=self.file_menu, label="File", underline=0)
        self.menubar.add_cascade(menu=self.view_menu, label="View", underline=0)

    def _create_statusbar(self):
        self.statusbar = Statusbar(self)

    def _on_open(self):
        formats = [('XML files', '*.xml'),
                   ('All files', '*.*'),
                   ]

        initialdir = os.getcwd()
        initialfile = "output.xml"
        filename = tkFileDialog.askopenfilename(parent=self, 
                                                filetypes=formats,
                                                initialfile = initialfile,
                                                initialdir = initialdir,
                                                title="Open")
        if filename is not None and filename != "":
            self.wm_title("%s - Robot Framework Workbench Log Viewer" % filename)
            self.viewer.refresh(filename)

    def _on_exit(self):
        self.destroy()
        sys.exit(0)


if __name__ == "__main__":
    app = LogViewerApp()
    app.mainloop()
