import Tkinter as tk
import ttk
import tkMessageBox
import tkFileDialog
import tkFont
import sys
import logging
import os
import imp
import urllib2
import platform
import subprocess
from rwb.widgets import Statusbar
from rwb.widgets import SearchEntry
from rwb.widgets import ToolButton
from rwb.images import data as icons
from rwb.lib.keywordtable import KeywordTable
from rwb.lib.configobj import ConfigObj
from rwb.lib.colors import ColorScheme
from rwb.lib.fonts import FontScheme
from about_dialog import AboutBoxDialog
from api import EditorAPI
from custom_notebook import CustomNotebook

# some things TODO:
# on focus out of the dte, set the cursor to a block
# on focus in of the dte, set the cursor to a thin line 
# (the thinking being, when the widget isn't focused it will
# be easier to see, but when typing it's less intrusive)
#
# move popup menu code to this file
#
# a tab at position 0 on a line, when the line is blank, should 
# insert either one or two pipes. One if the previous line is blank,
# two otherwise (?)
#

import os.path
here = os.path.abspath(os.path.dirname(__file__))
DEFAULT_SETTINGS = {
    "editor": {
        "recent files": [],
        },
    "extensions": {
        "transmogrifier": os.path.join(here, "extensions", "transmogrifier.py"),
        }
    }

DOCDIR = r'\\chiprodfs01\talos\Documentation'
MIN_FONT_SIZE = 8

class EditorApp(tk.Tk, EditorAPI):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        EditorAPI.__init__(self)

        self.colors = ColorScheme()
        self.fonts = FontScheme()

        self.extensions = {}

        s = ttk.Style()
        s.configure("Toolbutton", anchor="c")

        self._initialize_logging()
        self._initialize_preferences()
        self._initialize_keyword_database()
        self.loaded_files = {}
        self.wm_geometry("800x600")
        self._create_menubar()
        self._create_toolbar()
        self._create_statusbar()
        self._create_editor()
        self.statusbar.pack(side="bottom", fill="x")
        self.notebook.pack(side="top", fill="both", expand="true", pady=(4,0))
        self._add_bindings()

        for (name, path) in self.get_setting("editor.extensions", {}).iteritems():
            name = "extension_" + name
            self.extensions[name] = imp.load_source(name, path)
            self.extensions[name].__extend__(self)

        if (len(sys.argv)) > 1:
            self.after_idle(self.open, *sys.argv[1:])

        self.wm_title("Robot Framework Workbench")

    def save(self, page):
        '''Save the current page

        If the page doesn't have a file associated with it, ask
        the user for one.
        '''
        try:
            page.save()
            self.statusbar.message("saved to %s" % page.path)
        except Exception, e:
            message = "There was a problem saving the file."
            tkMessageBox.showwarning(parent=self, 
                                     title="Well, that sucks.",
                                     message="There was a problem saving the file",
                                     detail=str(e))


    def _update_recent_files_menu(self, filename=None):
        settings = self.get_settings("editor")
        filenames = settings.as_list("recent files")
        if filename is not None:
            filename = os.path.abspath(filename)
            if filename not in filenames:
                filenames.insert(0, filename)
                settings["recent files"] = filenames
                self.save_settings()

        # update the menu
        # WTF? This isn't working on windows
        self.recentFilesMenu.delete("@1", "end")

        for filename in filenames:
            self.recentFilesMenu.add_command(label=filename, 
                                             command=lambda filename=filename: self.open(filename))
        # MS Word, rarely a paragon of good design, has a "More..." item on the recent
        # files menu that opens up a dialog with a bunch of files. That's kinda cool.

    def _initialize_logging(self):
        formatter = logging.Formatter("%(levelname)s: %(module)s.%(funcName)s: %(message)s")
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        # this log level needs to come from settings or the
        # command line or something...
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(handler)
        self.log = logging.getLogger("rwb")

    def _initialize_preferences(self):
        if platform.system() == "Windows":
            settings_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
            settings_file = "rwb.cfg"
        else:
            settings_dir = os.environ.get("HOME", os.path.expanduser("~"))
            settings_file = ".rwb.cfg"
        settings_path = os.path.join(settings_dir, settings_file)
        self.log.debug("settings path: %s" % settings_path)
        
        self.settings = ConfigObj(DEFAULT_SETTINGS)
        try:
            user_settings = ConfigObj(settings_path)
            self.settings.merge(user_settings)
        except Exception, e:
            # need to report this somewhere useful, and 
            # make sure it has some useful information
            self.log.warning("error opening config file: %s" % str(e))
        
    def get_settings(self, category, default_settings = None):
        '''Return the settings for a given category

        A category is can be any sort of string; recommended
        procedure is for it to be a plugin ID (assuming I get 
        around to implementing plugins some day...)

        example:
            s = self.get_settings("editor", {"recent files": ['foo.txt', 'bar.txt']})
            print s["recent files"]
        '''

        if default_settings is not None and len(default_settings) > 0:
            # the configobj merge() method works backwards to how I 
            # want it to work. So create a dummy object, merge it with
            # the existing config data, then copy the config data for
            # this id back to the actual object
            tmp = ConfigObj({category: default_settings})
            tmp.merge(self.settings)
            self.settings[category] = tmp[category]
        return self.settings.setdefault(category, {})

    def _initialize_keyword_database(self):
        self.kwdb = KeywordTable()
        if os.path.exists(DOCDIR):
            self.kwdb.add_directory(DOCDIR)

    def get_search_target(self):
        '''Return the widget that should be the target of the search box'''
        return self.notebook.get_current_page().get_text_widget()

    def _create_toolbar(self):
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(side="top", fill="x")
        hr1 = ttk.Separator(self.toolbar, orient="horizontal")
        hr2 = ttk.Separator(self.toolbar, orient="horizontal")
        hr1.pack(side="top", fill="x")
        hr2.pack(side="bottom", fill="x")
        self.images = {}
        new = ToolButton(self.toolbar, imagedata=icons["page_add"],
                         text="new",
                         tooltip="Create a new test suite file",
                         command=lambda: self.event_generate("<<New>>"))
        save = ToolButton(self.toolbar, imagedata=icons["disk"],
                          text="save",
                          tooltip="save the document",
                          command=lambda: self.event_generate("<<Save>>"))
        cut = ToolButton(self.toolbar, imagedata=icons["cut"], 
                         text="cut",
                         tooltip="cut the selected text from the document",
                         command=lambda: self._send_event_to_focused_window("<<Cut>>"))
        copy = ToolButton(self.toolbar, imagedata=icons["page_copy"], 
                          text="copy",
                          tooltip="copy the selected text to the clipboard",
                          command=lambda: self._send_event_to_focused_window("<<Copy>>"))
        paste = ToolButton(self.toolbar, imagedata=icons["page_paste"], 
                           text="paste",
                           tooltip="paste the contents of the clipboard",
                           command=lambda: self._send_event_to_focused_window("<<Paste>>"))

        save.pack(side="left")
        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", fill="y", pady=8, padx=4)
        cut.pack(side="left")
        copy.pack(side="left")
        paste.pack(side="left")
        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", fill="y", pady=8, padx=4)

        self.searchentry  = SearchEntry(self, width=40)
        self.searchentry.pack(in_=self.toolbar, side="right", padx=(0,4))
        self.searchentry.bind("<Tab>", self._on_tab_in_search)

    def _on_tab_in_search(self, event):
        '''Handle tab key in search window

        This moves focus to the current text widget and cancels all the
        highlighting. The current match remains selected.
        '''
        # move to the current text widget
        page = self.notebook.get_current_page()
        self.searchentry.cancel()
        page.focus()
        return "break"

    def _add_bindings(self):
        keymap = self.get_setting("editor.keymap", None)
        if platform.system() == "Darwin":
            self.event_add("<<Open>>", "<Command-o>")
            self.event_add("<<Save>>", "<Command-s>")
            self.event_add("<<New>>", "<Command-n>")
            self.event_add("<<Popup>>", "<ButtonPress-2>")
            self.event_add("<<ZoomIn>>", "<Command-plus>")
            self.event_add("<<ZoomIn>>", "<Command-equal>")
            self.event_add("<<ZoomOut>>", "<Command-minus>")
            self.event_add("<<ZoomOut>>", "<Command-_>")
            self.event_add("<<Find>>", "<Command-f>")
            self.event_add("<<FindNext>>", "<Command-g>")
            self.event_add("<<FindNext>>", "<F3>")
        else:
            mod = "Alt" if keymap == "mac" else "Control"
            self.event_add("<<Open>>", "<%s-o>" % mod)
            self.event_add("<<Save>>", "<%s-s>" % mod)
            self.event_add("<<New>>", "<%s-n>" % mod)
            self.event_add("<<Popup>>", "<ButtonPress-3>")
            self.event_add("<<ZoomIn>>", "<%s-plus>" % mod)
            self.event_add("<<ZoomIn>>", "<%s-equal>" % mod)
            self.event_add("<<ZoomOut>>", "<%s-minus>" % mod)
            self.event_add("<<ZoomOut>>", "<%s-_>" % mod)
            self.event_add("<<Find>>", "<%s-f>" % mod)
            self.event_add("<<FindNext>>", "<%s-g>" % mod)
            self.event_add("<<FindNext>>", "<F3>")

            # untested:
            self.event_add("<<Close>>", "<Alt-F4>")
            self.event_add("<<CyclePage>>", "<Alt-Escape>")

        self.bind("<<Close>>", self._on_close)
        self.bind("<<Open>>", self.ask_open_file)
        self.bind("<<Save>>", self._on_save)
        self.bind("<<SaveAs>>", self._on_save_as)
        self.bind("<<New>>", self._on_new_file)
        self.bind("<<ZoomIn>>", self._on_zoom_in)
        self.bind("<<ZoomOut>>", self._on_zoom_out)
        self.bind("<<Find>>", self._on_find)
        self.bind("<<FindNext>>", self._on_find_next)

        # WTF? through trial and error I discovered that 
        # the "Text" widget class has a binding for button-2
        # which calls a ttk function. Srsly, WTF?
        self.bind_class("Text", "<Button-2>", None)

    def _on_find_next(self, event=None):
        self.searchentry.next()

    def _on_find(self, event=None):
        self.searchentry.focus()

    def _on_zoom_out(self, event=None):
        for font in (self.fonts.fixed, self.fonts.fixed_bold, self.fonts.fixed_italic):
            font.configure(size=max(MIN_FONT_SIZE, font.actual()["size"]-2))

    def _on_zoom_in(self, event=None):
        for font in (self.fonts.fixed, self.fonts.fixed_bold, self.fonts.fixed_italic):
            font.configure(size=max(MIN_FONT_SIZE, font.actual()["size"]+2))

    def _on_close(self, event=None):
        page = self.notebook.get_current_page()
        self.notebook.delete_page(page)

    def _on_save_as(self, event=None):
        page = self.notebook.get_current_page()

        if page.path is not None:
            initialfile = os.path.basename(page.path)
            initialdir  = os.path.dirname(initialfile)
        else:
            initialfile = page.name
            initialdir = os.getcwd()
            if not initialfile.endswith(".txt"):
                initialfile += ".txt"

        formats = [('Txt file', '*.txt'),
                   ('All files', '*.*'),
                   ]
        filename = tkFileDialog.asksaveasfilename(parent=self, 
                                                  filetypes=formats,
                                                  initialfile = initialfile,
                                                  initialdir = initialdir,
                                                  title="Save As...")
        if filename is not None:
            page.set_path(filename)
            self.save(page)

    def _on_save(self, event=None):
        page = self.notebook.get_current_page()
        if page.path is None:
            self._on_save_as(event)
        else:
            self.save(page)

    def _on_new_file(self, event=None):
        page = self.notebook.add_page(name="New Test")
#        page.bind("<<FileChanged>>", self._on_file_changed)

    def open(self, *args):
        '''Opens one or more files'''
        errors = []
        for path in args:
            try:
                self._load_file(path)
            except Exception, e:
                errors.append((path, e))
        if len(errors) == 1:
            message = "%s\n%s" % errors[0]
            tkMessageBox.showwarning("Error opening file",message)
        elif len(errors) > 1:
            message = "There were problems opening the following files:\n\n"
            for path, e in errors:
                if not (path.startswith("http")):
                    path = os.path.abspath(path)
                message += "%s\n%s\n\n" % (path, e)
            tkMessageBox.showwarning("Error opening file",message)
        
    def _load_file(self, filename):
        '''Load a file. If the filename is already loaded, select that tab'''

        try:
            existing_page = self.notebook.get_page_for_path(filename)
            if existing_page is not None:
                self.notebook.select_page(existing_page)
            else:
                new_page = self.notebook.add_page(filename)
                recent_files = self.get_setting("editor.recent files", [])
                recent_files.append(filename)
                self.save_settings()
                self._update_recent_files_menu(filename)

        except urllib2.HTTPError, e:
            raise e
        except IOError, e:
            raise Exception("No such file or directory")
        except Exception, e:
            raise e
        
#        page.bind("<<FileChanged>>", self._on_file_changed)

    def get_table_region(self, table):
        '''Return the range of lines for a robot table
        
        'table' must be one of "Test Cases", "Keywords", "Variables" or "Settings"

        Some rough timings show this only takes 1ms or so with a test
        file with 2k lines. Nice.
        '''
        
        if table not in ("settings","test cases", "keywords", "variables"):
            raise Exception("invalid table '%s': " % table +
                            "must be one of 'settings', " + 
                            "'test cases', 'keywords' or 'variables'")
        any_heading_pattern=r'^ *\*+[\* ]*(Test Cases?|(User )?Keywords?|Settings?|Variables?)[\* ]*$'
        # N.B. this pattern assumes 'table' is plural (note how
        # a '?' is appended immediately after the table name)
        heading_pattern = r'^ *\*+ *%s?[ \*]*$' % table
        start = self.dte.search(heading_pattern, "1.0", stopindex="end", regexp=True, nocase=True)
        if (start == ""): return (None, None)
        end = self.dte.search(any_heading_pattern, "%s lineend+1c" % start, 
                              stopindex="end", regexp=True, nocase=True)
        if end == "": end=self.dte.index("end")
        return (start, end)

    def ask_open_file(self, event):
        formats = [
            ("Robot plain text files", "*.txt"),
            ("HTML files", "*.html"),
            ("All files", "*.*"),
            ]
        f = tkFileDialog.askopenfilename(filetypes=formats,
                                         defaultextension=".txt",
                                         title="Open file")
        if f is not None:
            self.open(f)

    def _create_statusbar(self):
        self.statusbar = Statusbar(self)
        self.statusbar.add_section("modified", 8)

    def _create_editor(self):
        self.notebook = CustomNotebook(self, app=self)

    def _not_implemented_yet(self, *args):
        tkMessageBox.showwarning(parent=self, title="Well, that sucks.", 
                                                         message="Not implemented yet. Sorry!.")

    def _create_menubar(self):
        self.menubar = tk.Menu(self)
        self.configure(menu=self.menubar)

        self.recentFilesMenu = tk.Menu(self.menubar, tearoff=False)
        self._update_recent_files_menu()

        file_menu = tk.Menu(self.menubar, tearoff=False)
        accelerators = {}
        keymap = self.get_setting("editor.keymap", None)
        p = "Darwin" if keymap == "mac" else platform.system()
        # this is gross. 
        for p in ("Darwin", "Linux", "Windows"):
            if keymap == "mac" and platform != "Darwin":
                modifier = "Alt-"
            else:
                modifier = "Command" if p == "Darwin" else "Control"
            accelerators[p] = {
                "find": modifier + "-F",
                "find_next": modifier + "-G",
                "undo": modifier + "-Z",
                "redo": modifier + "-Y",
                "save": modifier + "-S",
                "open": modifier + "-O",
                "new":  modifier + "-N",
                "cut":  modifier + "-X",
                "copy": modifier + "-C",
                "paste": modifier + "-V",
                "zoomin": modifier + "-+",
                "zoomout": modifier + "--",
                "exit": modifier + "-Q",
                }

        file_menu.add_command(label="New",
                             accelerator=accelerators[p]["new"],
                             command=lambda: self.event_generate("<<New>>"))
        file_menu.add_command(label="Open...", 
                             accelerator=accelerators[p]["open"],
                             command=lambda: self.event_generate("<<Open>>"))
        file_menu.add_cascade(label="Open Recent",
                             menu = self.recentFilesMenu)
        file_menu.add_command(label="Save",
                             accelerator=accelerators[p]["save"],
                             command=lambda: self.event_generate("<<Save>>"))
        file_menu.add_command(label="Save As...",
                             command=lambda: self.event_generate("<<SaveAs>>"))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", 
                             accelerator=accelerators[p]["exit"],
                             command=self.OnExit)
        self.menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(self.menubar, tearoff=False)
        edit_menu.add_command(label="Find", underline=0,
                             accelerator=accelerators[p]["find"],
                             command=lambda: self._send_event_to_focused_window("<<Find>>"))
        edit_menu.add_command(label="Find Next", underline=5,
                             accelerator=accelerators[p]["find_next"],
                             command=lambda: self._send_event_to_focused_window("<<FindNext>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Undo", underline=0,
                             accelerator=accelerators[p]["undo"],
                             command=lambda: self._send_event_to_focused_window("<<Undo>>"))
        edit_menu.add_command(label="Redo", underline=0,
                             accelerator=accelerators[p]["redo"],
                             command=lambda: self._send_event_to_focused_window("<<Redo>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", underline=2, 
                             accelerator=accelerators[p]["cut"],
                             command=lambda: self._send_event_to_focused_window("<<Cut>>"))
        edit_menu.add_command(label="Copy", underline=0, 
                             accelerator=accelerators[p]["copy"],
                             command=lambda: self._send_event_to_focused_window("<<Copy>>"))
        edit_menu.add_command(label="Paste", underline=0, 
                             accelerator=accelerators[p]["paste"],
                             command=lambda: self._send_event_to_focused_window("<<Paste>>"))
        self.menubar.add_cascade(label="Edit", menu=edit_menu)

        view_menu = tk.Menu(self.menubar, tearoff=False)
        zoom_menu = tk.Menu(self.menubar, tearoff=False)
        view_menu.add_cascade(label="Zoom", menu=zoom_menu)
        zoom_menu.add_command(label="Zoom In", 
                             accelerator=accelerators[p]["zoomin"],
                             command=lambda: self.event_generate("<<ZoomIn>>"))
        zoom_menu.add_command(label="Zoom Out", 
                             accelerator=accelerators[p]["zoomout"],
                             command=lambda: self.event_generate("<<ZoomOut>>"))
        self.menubar.add_cascade(label="View", menu=view_menu)

        table_menu = tk.Menu(self.menubar, tearoff=False)
        table_menu.add_command(label="Select similar rows", command=self._on_select_similar_rows)
        table_menu.add_separator()
        table_menu.add_command(label="Align Cells", command=self._on_align_rows)
        table_menu.add_command(label="Compress Cells", command=self._on_compress_rows)

        self.menubar.add_cascade(label="Table", menu=table_menu)

        tools_menu = tk.Menu(self.menubar, tearoff=False, postcommand=self._on_post_tools_menu)
        self.menubar.add_cascade(label="Tools", underline=3, menu=tools_menu)

        # toolsMenu = tk.Menu(self.menubar, tearoff=False)
        # # eventually this will be loaded from a plugin interface;
        # # for now this simulates that
        # from stubber import StubTool
        # stubber = StubTool()
        # self.tools = [stubber]
        # toolsMenu.add_command(label=stubber.label,
        #                       command=lambda tool=stubber: self._invoke_tool(tool))
        # self.menubar.add_cascade(label="Tools", menu=toolsMenu)

        run_menu = tk.Menu(self.menubar, tearoff=False)
        run_menu.add_command(label="Run current test suite", command=self._on_run_current)
        run_menu.add_command(label="Dry run of current test suite", command=self._on_dry_run)
        self.menubar.add_cascade(label="Run", menu=run_menu)

        help_menu = tk.Menu(self.menubar, tearoff=False)
        help_menu.add_command(label="View Help", command=self._on_view_help)
        help_menu.add_command(label="View Shortcuts", command=self._on_view_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About the workbench editor", command=self._on_about)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        # keep public versions, so extensions can extend them
        self.file_menu = file_menu
        self.edit_menu = edit_menu
        self.view_menu = view_menu
        self.table_menu = table_menu
        self.tools_menu = tools_menu
        self.help_menu = help_menu
        self.run_menu = run_menu

    def _run(self, *args):
        cmd = "python -m rwb.runner " + " ".join(['%s' % x for x in args])
        print "cmd:", cmd
        os.system(cmd + "&")

    def _on_dry_run(self, event=None):
        page = self.notebook.get_current_page()
        if page.path is None:
            message = "You must first save this to a file before running"
            tkMessageBox.showwarning(parent=self, 
                                     title="Sorry about this...",
                                     message=message)
            return
        self.save(page)
        self._run("--runmode", "DryRun", page.path)
        
    def _on_run_current(self, event=None):
        page = self.notebook.get_current_page()
        if page.path is None:
            message = "You must first save this to a file before running"
            tkMessageBox.showwarning(parent=self, 
                                     title="Sorry about this...",
                                     message=message)
        else:
            self.save(page)
            cmd = "python -m rwb.runner '%s'" % page.path
            os.system(cmd + "&")
        return "break"

    def _on_select_similar_rows(self):
        current_editor = self.get_current_editor()
        current_editor.select_similar_rows()
        
    def _on_align_rows(self):
        current_editor = self.get_current_editor()
        current_editor.align_rows()

    def _on_compress_rows(self):
        current_editor = self.get_current_editor()
        current_editor.compress_rows()
        
    def _on_post_tools_menu(self):
        current_editor = self.get_current_editor()
        for f in self._tools:
            f.update(current_editor)
        
    def _on_view_shortcuts(self):
        import help
        # need to determine if we already have a shortcut 
        # page, and only create it if it doesn't exist. 
        page = self.notebook.add_custom_page(page_class=help.ShortcutPage)
        
    def _on_view_help(self):
        import help
        page = self.notebook.add_custom_page(page_class=help.HelpPage)

    def _on_about(self):
        dialog = AboutBoxDialog(self)

    def _invoke_tool(self, tool):
        tool.invoke(self.notebook.get_current_page())

    def _send_event_to_focused_window(self, event):
        '''Send an event to the window with focus'''
        widget = self.focus_get()
        widget.event_generate(event)

    def OnExit(self):
        self.destroy()



if __name__ == "__main__":
    app = RWB()
    app.mainloop()
