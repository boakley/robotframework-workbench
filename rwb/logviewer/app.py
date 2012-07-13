import sys
import os
import Tkinter as tk
import ttk
from rwb.lib import AbstractRwbGui
from rwb.widgets import Statusbar, ToolButton
from rwb.lib.configobj import ConfigObj
from logviewer import LogTree
import tkFileDialog
import tkMessageBox
import argparse

NAME="logviewer"
DEFAULT_SETTINGS = {
    NAME: {}
}

class LogViewerApp(AbstractRwbGui):
    def __init__(self):
        args = self._parse_args()

        AbstractRwbGui.__init__(self, NAME, DEFAULT_SETTINGS, args)

        self._create_menubar()
        self._create_toolbar()
        self._create_statusbar()

        vsb = ttk.Scrollbar(self, orient="vertical")
        self.viewer = LogTree(self, fail_only=self.args.fail_only, condensed=self.args.condensed)
        vsb.configure(command=self.viewer.tree.yview)
        self.viewer.tree.configure(yscrollcommand=vsb.set)
        self.toolbar.pack(side="top", fill="x")
        self.statusbar.pack(side="bottom", fill="x")
        vsb.pack(side="right", fill="y")
        self.viewer.pack(side="top", fill="both", expand=True)
        self.viewer.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        if self.args.file != None:
            self.after_idle(self.after, 1, lambda path=self.args.file: self.open(path))
#            self.after_idle(self.after, 1, lambda path=sys.argv[1]: self.open(path))

        self.wm_geometry("1000x800")

    def _parse_args(self):
        '''Parse command line arguments'''
        parser = argparse.ArgumentParser(prog="rwb.logviewer")
        parser.add_argument("file",nargs="?",
                            help="the path to a robot output file (eg: output.xml)")
        parser.add_argument("-f", "--fail-only", action="store_true",
                            help="only display failed suites, tests and keywords")
        parser.add_argument("-c", "--condensed", action="store_true",
                            help="don't auto-expand failed keyworeds")
        return parser.parse_args()

    def _on_select(self, event):
        selection = self.viewer.tree.selection()
        self.log.debug("selection: %s" % selection)
        if len(selection) > 0:
            item = selection[0]
            self.log.debug("item: %s" % item)
            self.log.debug("tags: %s" % ",".join(self.viewer.tree.item(item, "tags")))
            self.log.debug("values: %s" % ",".join(self.viewer.tree.item(item, "values")))
            x = self.viewer.tree.item(item, "values")[-1]

    def _create_toolbar(self):
        self.toolbar = ttk.Frame(self)
        suite_button = ToolButton(self.toolbar, text="Suites", width=0,
                                  tooltip="Expand to show all suites")
        test_button = ToolButton(self.toolbar, text="Test Cases",  width=0,
                                 tooltip="Expand to show all suites and test cases")
        kw_button = ToolButton(self.toolbar, text="Test Keywords",  width=0,
                               tooltip="Expand to show all suites, test cases, and their keywords")
        all_button = ToolButton(self.toolbar, text="Expand All Keywords", width=0,
                                tooltip="Expand to show all suites, test cases, and keywords")

        # this is just for experimentation; I don't really plan to have this on the toolbar
        next_fail = ToolButton(self.toolbar, text="Next Failure", width=0,
                               tooltip="Go to next failed keyword", command=self._on_next_fail)
        prev_fail = ToolButton(self.toolbar, text="Previous Failure", width=0,
                               tooltip="Go to previous failed keyword", command=self._on_previous_fail)

        suite_button.pack(side="left")
        test_button.pack(side="left")
        kw_button.pack(side="left")
        all_button.pack(side="left")
        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", padx=4, pady=2, fill="y")
        next_fail.pack(side="left")
        prev_fail.pack(side="left")

    def _on_next_fail(self):
        item = self.viewer.next_with_tag("FAIL")
        if item is not None and item != "":
            self.viewer.tree.see(item)
            if self.viewer.tree.bbox(item) == "":
                # for some reason, that previous call to .see() doesn't always
                # scroll the item into view. If we detect that, it means it
                # is off screen so lets call see() again, then scroll up a 
                # few lines to show some context.
                self.after_idle(self.viewer.tree.see, item)
                self.after_idle(self.viewer.tree.yview_scroll,4, "units")
            self.viewer.tree.focus(item)
            self.viewer.tree.selection_set(item)

    def _on_previous_fail(self):
        item = self.viewer.previous_with_tag("FAIL")
        if item is not None and item != "":
            self.viewer.tree.see(item)
            if self.viewer.tree.bbox(item) == "":
                # for some reason, that previous call to .see() doesn't always
                # scroll the item into view. If we detect that, it means it
                # is off screen so lets call see() again, then scroll up a 
                # few lines to show some context.
                self.after_idle(self.viewer.tree.see, item)
                self.after_idle(self.viewer.tree.yview_scroll,-4, "units")
            self.viewer.tree.focus(item)
            self.viewer.tree.selection_set(item)
        
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
        self.view_menu.add_command(label="All Keywords", underline=0, 
                                   command=self._on_expand_all)

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
            self.open(filename)

    def open(self, path):
        try:
            self.viewer.refresh(path)
            self.wm_title("%s - Robot Framework Workbench Log Viewer" % path)
        except Exception, e:
            print "WTF?", e
            tkMessageBox.showwarning("Unable to open the file\n\n%s" % str(e))
            self.wm_title("Robot Framework Workbench Log Viewer")

    def _on_expand_all(self):
        self.viewer.expand_all()

    def _on_exit(self):
        self.destroy()
        sys.exit(0)


if __name__ == "__main__":
    app = LogViewerApp()
    app.mainloop()
