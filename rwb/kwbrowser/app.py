'''
'''

import os
import sys
import Tkinter as tk
import tkFileDialog, tkMessageBox
import ttk
from rwb.widgets import AutoScrollbar
from rwb.widgets import Statusbar
from kwbrowser import KwBrowser

class KwBrowserApp(tk.Tk):
    '''A Tkinter application that wraps the browser frame'''
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.working_set = sys.argv[1:]

        self.wm_title("RWB Keyword Browser")
        self.kwt = KwBrowser(self, borderwidth=1, relief="solid")
        menubar = Menubar(self)
        self.statusbar = Statusbar(self)
        self.statusbar.pack(side="bottom", fill="x")
        self.kwt.pack(side="top", fill="both", expand=True, padx=4)
        self.bind("<<Reload>>", lambda event: self.reload())
        self.bind("<<LoadFile>>", lambda event: self.load_resource())
        self.configure(menu=menubar)
        self.reload()

    def load_resource(self, filename=None):
        '''Load a resource after prompting the user'''
        if filename is None:
            filename = tkFileDialog.askopenfilename(defaultextension=".txt",
                                                    title="Open Robot resource or test suite file",
                                                    filetypes=[('all files', "*"),
                                                               ('.txt files', "*.txt"),
                                                               ('.html files', "*.html")])
        if filename is not None:
            try:
                self.kwt.add_file(filename)
                self.working_set.append(filename)
            except Exception, e:
                print "drat!", e
                tkMessageBox.showinfo(
                    "Load file...",
                    "The file does not appear to be a resource file, test suite or libdoc output file",
                    parent=self
                    )

    def reload(self):
        '''(Re)load the libdoc files

        This will load all of the .xml files in docDir, and any
        filenames that were on the command line.

        Ideally we should automatically reload if we notice the
        data source(s) has changed on disk. For now this is good
        enough
        '''
        self.kwt.reset()

        self.kwt.add_library("BuiltIn")
        for path in self.working_set:
            if os.path.isdir(path):
                for filename in os.listdir(path):
                    if (filename.endswith(".xml") or 
                        filename.endswith(".txt") or
                        filename.endswith(".tsv")):
                        self.kwt.add_file(os.path.join(path, filename))
            else:
                self.kwt.add_file(path)

    def _load_dir(self, path):
        for filename in os.listdir(docDir):
            if filename.endswith(".xml"):
                path = os.path.join(docDir, filename)
                self.kwt.add_file(path)

class Menubar(tk.Menu):
    '''A menubar for the KeywordTool application'''
    def __init__(self, parent, *args, **kwargs):
        tk.Menu.__init__(self, parent, *args, **kwargs)
        self.fileMenu= tk.Menu(self, tearoff=False)
        self.fileMenu.add_command(label="Load File...", 
                                  command=lambda: parent.event_generate("<<LoadFile>>"))
        self.fileMenu.add_command(label="Reload", command=lambda: parent.event_generate("<<Reload>>"))
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Exit", command=lambda: sys.exit(0))
        self.add_cascade(label="File", menu=self.fileMenu)

