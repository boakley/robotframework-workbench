'''
RWB Keyword Browser

A tool for browsing robotframework keywords
'''

import os
import sys
import Tkinter as tk
import tkFileDialog, tkMessageBox
import ttk
import robot.libraries
from rwb.widgets import AutoScrollbar
from rwb.widgets import Statusbar
from rwb.lib import AbstractRwbApp
from kwbrowser import KwBrowser

class KwBrowserApp(AbstractRwbApp):
    '''A Tkinter application that wraps the browser frame'''
    def __init__(self, *args, **kwargs):
        AbstractRwbApp.__init__(self, "rwb.kwbrowser")
        self.wm_geometry("800x600")
        self.working_set = sys.argv[1:]

        self.wm_title("Keyword Browser - Robot Framework Workbench")
        self.kwt = KwBrowser(self, borderwidth=1, relief="solid")
        menubar = Menubar(self)
        self.statusbar = Statusbar(self)
        self.statusbar.pack(side="bottom", fill="x")
        self.kwt.pack(side="top", fill="both", expand=True, padx=4)
        self.bind("<<Reload>>", lambda event: self.reload())
        self.bind("<<LoadFile>>", lambda event: self.load_resource())
        self.configure(menu=menubar)
        self.reload()

    def reload(self):
        '''(Re)load the libdoc files

        This will load all of the .xml files in docDir, and any
        filenames that were on the command line.

        Ideally we should automatically reload if we notice the
        data source(s) has changed on disk. For now this is good
        enough
        '''
        self.kwt.reset()

        # try to load all libraries installed with robot
        # I'm not a big fan of this solution but I like the
        # end result, so I deem it Good Enough for now.
        libdir = os.path.dirname(robot.libraries.__file__)

        loaded = []
        for filename in os.listdir(libdir):
            if filename.endswith(".py") or filename.endswith(".pyc"):
                libname, ext = os.path.splitext(filename)
                if (libname.lower() not in loaded and 
                    not self._should_ignore(libname)):

                    # N.B. remote library has no default constructor
                    # so to speak; importing it will fail because it
                    # requires an argument.
                    try:
                        self.log.debug("adding library '%s'" % libname)
                        self.kwt.add_library(libname)
                        loaded.append(libname.lower())
                    except Exception, e:
                        # need a better way to log this...
                        self.log.debug("unable to add library: " + str(e))

        for path in self.working_set:
            if os.path.isdir(path):
                for filename in os.listdir(path):
                    if (filename.endswith(".xml") or 
                        filename.endswith(".txt") or
                        filename.endswith(".tsv")):
                        try:
                            fullname = os.path.join(path, filename)
                            self.kwt.add_file(fullname)
                        except Exception, e:
                            message = "unable to load '%s'" % fullname
                            message += ": " + str(e)
                            self.log.warning(message)
            else:
                try:
                    self.kwt.add_file(path)
                except Exception, e:
                    message = "unable to load '%s'" % path
                    message += ": " + str(e)
                    self.log.warning(message)

    def _should_ignore(self, name):
        '''Return True if a given library name should be ignored'''
        _name = name.lower()
        return (_name.startswith("deprecated") or
                _name.startswith("_") or
                _name == "remote" or
                _name == "easter")

    def load_resource(self, filename=None):
        '''Load a resource file'''
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
                tkMessageBox.showinfo(
                    "Load file...",
                    "The file does not appear to be a resource file, test suite or libdoc output file",
                    parent=self
                    )

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

