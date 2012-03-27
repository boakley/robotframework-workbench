'''EditorPage - one page in a CustomNotebook'''

import Tkinter as tk
import ttk
#from core.dte import DynamicTableEditor
from rwb.widgets import DynamicTableEditor
from dte_margin import DteMargin
from rwb.widgets import AutoScrollbar
import codecs
import re
import os
import sys
import tkFont
import platform
from rwb import FONT_SCHEME, COLOR_SCHEME
import urllib2

# I hate to hard-code these, but I don't think there's a robot 
# API I can use to get them. 
AUTOMATIC_VARS = [ "${TEST NAME}", "${TEST STATUS}", "${TEST MESSAGE}",
                   "${PREV TEST NAME}", "${PREV TEST STATUS}",
                   "${PREV TEST MESSAGE}", "${SUITE NAME}",
                   "${SUITE SOURCE}", "${SUITE STATUS}", "${SUITE MESSAGE}",
                   "${OUTPUT FILE}", "${LOG FILE}", "${REPORT FILE}",
                   "${DEBUG FILE}", "${OUTPUT DIR}" ]
KEYWORD_SETTINGS = ["[Documentation]", "[Arguments]", "[Return]",
                    "[Teardown]", "[Timeout]"]
TESTCASE_SETTINGS = ["[Documentation]", "[Tags]", "[Setup]", 
                     "[Teardown]", "[Template]", "[Timeout]"
                     "[Force Tags]", "[Default Tags]",
                     "[Test Setup]", "[Test Teardown]",
                     "[Test Template]", "[Test Timeout]"]

class EditorPage(tk.Frame):
    '''This class represents one "page" in the editor notebook

    Since Tkinter text widgets manage their data, this class
    will not keep its own copy in a property in order to cut
    down on memory usage.
    '''
    encoding = "ascii"
    parent = None
    notebook = None
    is_uri = False
    is_readonly = False

    def __init__(self, parent, path=None, name=None, app=None):
        self.parent = parent
        self.app = app
        self.path = path
        self.name = name
        if name is None and path is not None:
            self.name = os.path.basename(path)

        if path is not None:
            if path.split(":", 1)[0].lower() in ("http", "https"):
                self.is_uri = True
                self.is_readonly = True
            else:
                self.path = os.path.abspath(self.path)
        self._name_var = tk.StringVar()
        self._name_var.trace("w", self._on_name_trace)

        tk.Frame.__init__(self, parent)
        self._create_widgets()
#        self.configure(background=self.app.colors.background2)

        # keep track of window height; when it changes, don't
        # immediately update the line numbers
        self._last_winfo_height = self.winfo_height()

        if path is not None and os.path.exists(path):
            self.load(path)

    def _on_linenumber_control_click(self, event):
        text_index = self.dte.index("@%s,%s" % (event.x, event.y))
        self.dte.mark_set("click", "%s linestart" % text_index)
        self.dte.tag_add("sel", "%s linestart" % text_index, "%s lineend+1c" % text_index)
        
    def _on_linenumber_click(self, event):
        try:
            text_index = self.dte.index("@%s,%s" % (event.x, event.y))
            self.dte.mark_set("click", "%s linestart" % text_index)
            self.dte.tag_remove("sel", "1.0", "end")
            self.dte.tag_add("sel", "%s linestart" % text_index, "%s lineend+1c" % text_index)
            self.dte.mark_set("insert", "%s linestart" % text_index)
        except Exception, e:
            print "drat:", e
            import sys; sys.stdout.flush()

    def _on_linenumber_move(self, event):
        try:
            text_index = self.dte.index("@%s,%s" % (event.x, event.y))
            self.dte.tag_remove("sel", "1.0", "end") 
            if self.dte.compare(text_index, ">", "click"):
                self.dte.tag_add("sel", "click", "%s lineend+1c" % text_index)
            else:
                self.dte.tag_add("sel", "%s linestart" % text_index, "click lineend+1c")
            self.dte.mark_set("insert", "%s lineend" % text_index)
        except Exception, e:
            print "drat:", e

    def _on_name_trace(self, *args):
        self.name = self._name_var.get()
        self.event_generate("<<NameChanged>>")

    def focus(self):
        self.dte.focus_set()

    def toggle_linenumbers(self, show=None):
        if show is None:
            show = not self.linenumbers.winfo_visible()
        if show:
            self.linenumbers.grid()
        else:
            self.linenumbers.grid_remove()

    def get_row(self, linenumber):
        return self.dte.get_row(linenumber)

    def get_text(self):
        return self.dte.get(1.0, "end-1c")

    def set_path(self, path):
        '''Sets the path associated with this page'''
        self.path = path
        self.name = os.path.basename(path)
        self.namepath.configure(text=path)
        # I do not know why, but this code sometimes crashes on my box
        # if I remove the following statement. WTF?
        sys.stdout.flush()
        self._name_var.set(self.name)

    def _create_widgets(self):
        self.nameframe = tk.Frame(self, background='white')
        self.nameentry = tk.Entry(self.nameframe, relief="flat", 
                                  font=("Helvetica", 16, "normal"), 
                                  insertbackground="#ff0000",
                                  insertwidth=1,
                                  highlightthickness=0,
                                  textvariable = self._name_var)
        self.close_button = tk.Button(self.nameframe, text="close [x]", 
                                      borderwidth=1, relief="raised",
                                      highlightthickness=0,
                                      foreground="white",
                                      command=lambda: self.dte.event_generate("<<Close>>"))
        self.nameentry.insert(0, self.name)
#        self.nameentry.pack(fill="both", expand="True")
        self.namepath = tk.Label(self.nameframe, 
                                 text="<unsaved>",
                                 anchor="sw", borderwidth=0, foreground="gray")
#                                 background=core.colors.background3)
        if self.path is not None:
            self.namepath.configure(text=self.path)
#        hr = tk.Frame(self.nameframe, background=core.colors.background2, borderwidth=0, height=1)
        hr = tk.Frame(self.nameframe, borderwidth=0, height=1)
#        self.namepath.pack(side="bottom", fill="x")
#        hr.pack(side="bottom", fill="x", padx=8)
        self.nameentry.grid(row=0, column=0, sticky="nsew")
        self.close_button.grid(row=0, column=1, sticky="e", padx=4, ipadx=4)
        hr.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.namepath.grid(row=2, column=0, columnspan=2, sticky="nswe")
        self.nameframe.grid_columnconfigure(0, weight=1)

        em = self.app.fonts.fixed.measure("M")
        tabwidth = 2 # needs to be a user preference...
        # wrapping doesn't play well with auto horizontal
        # scrollbars...  if we allow word wrapping we need to turn off
        # the horizontal scrollbar...
        wrap = "none" 
        self.dte = DynamicTableEditor(self, borderwidth=0,
                                      insertbackground="#ff0000",
                                      wrap=wrap,
                                      insertwidth=1,
                                      highlightthickness=0,
                                      tabstyle="wordprocessor",
                                      undo=True, autoseparators=True,
                                      tabs = tabwidth*em,
                                      font=self.app.fonts.fixed)

        self.linenumbers = DteMargin(self, background="#f2f2f2",
                                     borderwidth=0,
#        self.linenumbers = DteMargin(self, borderwidth=0,
                                     highlightthickness=0, width=4*em)
        self.linenumbers.attach(self.dte)
        self.configure(background=self.dte.cget("background"))
        vsb = AutoScrollbar(self,
                            command=self.dte.yview, 
                            orient="vertical")
        hsb = AutoScrollbar(self,
                            command=self.dte.xview, 
                            orient="horizontal")
        filler = tk.Frame(self, 
                          borderwidth=0, highlightthickness=0)
#        filler = tk.Frame(self, borderwidth=0, highlightthickness=0)
        self.dte.configure(xscrollcommand=hsb.set, yscrollcommand=self.OnYviewChanged)
        self.linenumbers.grid(row=1, column=0, sticky="ns", padx=0, pady=4, ipadx=2)
        self.nameframe.grid(row=0, column=1, sticky="nsew", columnspan=2)
        filler.grid(row=0, column=0, sticky="nsew", padx=0)
        self.dte.grid(row=1, column=1, sticky="nsew", padx=4, pady=4)
        vsb.grid(row=1, column=2, sticky="ns", pady=(4,0))
        hsb.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.vsb = vsb

        self._define_tags()

        self.dte.add_post_change_hook(self.OnDTEChange)
#        self.dte.bind("<Configure>", lambda event: self.draw_line_numbers())
        self.dte.bind("<<AutoComplete>>", self.on_autocomplete)
        self.dte.bind("<*>", self.on_star)

        self.popup_menu = tk.Menu(self.dte, tearoff=False)
        self.popup_menu.add_command(label="Cut", underline=2, 
                                   command=lambda: self.dte.event_generate("<<Cut>>"))
        self.popup_menu.add_command(label="Copy", underline=0, 
                                   command=lambda: self.dte.event_generate("<<Copy>>"))
        self.popup_menu.add_command(label="Paste", underline=0, 
                                   command=lambda: self.dte.event_generate("<<Paste>>"))
        self.popup_menu.add_separator()
        self.popup_menu.add_cascade(label="Tools", menu=self.app.tools_menu)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label="Close this file", 
                                   command=lambda: self.dte.event_generate("<<Close>>"))

        # hmmm; on my mac the right button does a "<2>",
        # but on windows it does a "<3>"
        self.dte.bind("<<Popup>>", self.on_popup)

        # I don't know why, but on the mac there's a ButtonRelease-2
        # binding on something that seems to paste the selection.
        # this turns that off.
        self.dte.bind("<ButtonRelease-2>", lambda event: "break")

#        self.notebook.add(self, text=os.path.basename(name))
#        self.notebook.select(self)

    def _compute_checksum(self):
        text = self.dte.get(1.0, "end-1c")
        try:
            import zlib
            encoded_text = text.encode(self.encoding)
            self._checksum = zlib.adler32(encoded_text)
        except Exception, e:
            print "hey, computing the checksum failed:", e


    def save(self):
        self._checksum = self._compute_checksum()
        # For saving we'll strip off all trailing whitespace and
        # ensure the text ends with a newline.
        text = self.dte.get(1.0, "end-1c").rstrip() + "\n"
        if self.encoding == "ascii" and not self._is_ascii(text):
            self.app.status_message("unicode detected; switching to utf-8")
            self.encoding="utf-8-sig"
        encoded_text = text.encode(self.encoding)
        with open(self.path, "w") as f:
            f.write(encoded_text)

    def _is_ascii(self, s):
        try:
            s.decode('ascii')
            return True
        except UnicodeEncodeError:
            return False

    def get_text_widget(self):
        '''Return the text widget associated with this page'''
        return self.dte

    def on_autocomplete(self, event):
        line = self.dte.get("insert linestart", "insert lineend")
        if line.startswith("*"):
            # I'm not crazy about this; I don't like putting the
            # "***" in the choices, but for now its necessary 
            # because the widget doesn't recognize the words 
            # between the leading "***" and trailing "***" as 
            # a cell -- meaning, the choice overrides the whole
            # line. 
            self.dte.set_completion_choices(["*** Test Cases ***", 
                                             "*** Keywords ***", 
                                             "*** Settings ***", 
                                             "*** Variables ***"])
        else:
            try:
                cell_contents = self.dte.get("current_cell.first", "current_cell.last")
                cell_contents = cell_contents.lower()
            except tk.TclError:
                return

            if cell_contents.startswith("["):
                # I need to determine which table the cursor is in
                # and make the list correct for the table...
                meta = set(KEYWORD_SETTINGS + TESTCASE_SETTINGS)
                choices = [s for s in meta if s.lower().startswith(cell_contents)]
                self.dte.set_completion_choices(choices)

            elif cell_contents.startswith("${"):
                # HMMM. This fails completely if the user types something
                # like ${foo}${bar}...  in a perfect world the completion
                # is on a word, but keywords can have spaces so we can't
                # do that.
                local_vars = re.findall(r'\${.*?}', self.dte.get(1.0, "insert"))
                varnames = sorted(set(local_vars + AUTOMATIC_VARS))
                choices = [s for s in varnames if s.lower().startswith(cell_contents.rstrip("}"))]
                self.dte.set_completion_choices(choices)
                
            else:
                keywords = sorted(self.app.kwdb.get_keywords())
                choices = [s for s in keywords if s.lower().startswith(cell_contents)]
                self.dte.set_completion_choices(choices)

    def on_popup(self, event=None):
        self.popup_menu.tk_popup(event.x_root, event.y_root)

    def on_star(self, event):
        '''If the user types '*' on an otherwise blank line, insert '*** ***' 
        then place cursor in the middle
        '''
        if self.dte.compare("insert linestart", "==", "insert lineend"):
            # must be a new, blank line
            self.dte.insert("insert", "***   ***\n| ")
            self.dte.mark_set("insert", "insert linestart -1 line + 4c")
            self.dte.see("insert+1line")
            return "break"

    def on_close(self):
        print "closing!"

    def load(self, path):
        '''Load a file given by the filename'''
        if self.path is None:
            raise Exception("nothing to load")

        self.dte.delete(1.0, "end")
        if path.startswith("http:") or path.startswith("https:"):
            f = urllib2.urlopen(self.path)
        else:
            f = open(self.path, "rU")
        data = f.read().replace("\r\n", "\n")
        f.close()

        # hmmm; this will cause problems if the very last line
        # of a file ends in backspace-space. What's the
        # likelihood of that happening?
        data = data.rstrip()
        if data.startswith(codecs.BOM_UTF8):
            # N.B. visual studio creates utf-8 files with a
            # BOM as the first character.  We need to remove
            # the BOM, otherwise it will appear as a garbage
            # character in the text widget.
            data = data.decode("utf-8-sig")
            self.encoding="utf-8-sig"
        else:
            self.encoding="ascii"
        self.dte.insert(1.0, data)
        self.dte.edit_reset()
        self.dte.mark_set("insert", 1.0)
        self._checksum = self._compute_checksum()

    def get_test_cases(self):
        regions = self.get_table_regions("test cases")
        testcases = []
        for (start, end) in regions:
            indexes = self.tk.call(str(self.dte), "search", "-all", "-regexp",
                                   r'^ *\| *([^|\s].+)$', start, end)
            for index in indexes:
                line = self.dte.get(str(index), "%s lineend" % str(index))
                testcases.append(line.strip("| "))
        return testcases

    def get_table_regions(self, table):
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
        result = []
        end = "1.0"
        while True:
            start = self.dte.search(heading_pattern, end, stopindex="end", regexp=True, nocase=True)
            if (start == ""): break
            end = self.dte.search(any_heading_pattern, "%s lineend+1c" % start, 
                                  stopindex="end", regexp=True, nocase=True)
            if end == "": end=self.dte.index("end")
            result.append((start, end))
        return result

    def _define_tags(self):
        FORESTGREEN="#228b22"
        FIREBRICK="#b22222"
        DARKBLUE="#00006f"

        self.dte.tag_configure("name", foreground=FORESTGREEN, 
                               font=self.app.fonts.fixed_bold)
        self.dte.tag_configure("ellipsis", foreground="lightgray")
        self.dte.tag_configure("heading", font=self.app.fonts.fixed_bold, background="gray")
        self.dte.tag_configure("variable", foreground=DARKBLUE, 
                               font=self.app.fonts.fixed_bold)
        self.dte.tag_configure("noise", foreground="lightgray")
        self.dte.tag_configure("comment", foreground=FIREBRICK)
        self.dte.tag_configure("bold", font=self.app.fonts.fixed_bold)
        # make sure this is last so it has higher priority than the 
        # other tags
        self.dte.tag_configure("column_marker", foreground="lightgray")

        # make sure the selection has highest precedence; otherwise, selecting blue
        # text (assuming the selection is blue) obscurs the text. 
        self.dte.tag_raise("sel")

    def OnYviewChanged(self, *args):
        '''Handle scrolling of widget and updating line numbers

        This gives dreadful performance when the user resizes the window,
        since each pixel change in the size causes the line numbers to
        recalculate. I need to figure out how to optimize for that case...
        '''
        result = self.vsb.set(*args)
        self.linenumbers.update_linenumbers()
        return result

    def OnDTEChange(self, *args):
        '''Called after a material change to the text widget contents

        First element of *args will be the text widget commannd
        that caused the change ("insert", "delete", or "replace")
        the rest of the arguments will vary depending on that
        command
        '''
        # make sure there is always a newline at the end (well, two
        # newlines since tk always adds one). Why? So the user
        # always has a blank line on which to click. It's just a 
        # little usability thing
        if (self.dte.get("end-2c", "end") != "\n\n"):
            insert = self.dte.index("insert")
            self.dte.insert("end", "\n")
            self.dte.mark_set("insert", insert)

        # remove all special tags
        block_start = self.dte.index("start_change linestart")
        block_end = self.dte.index("end_change lineend +1c")
        for tag in ("name", "variable", "noise","heading", 
                    "comment", "keyword", "bold", "cell", "ellipsis"):
            self.dte.tag_remove(tag, block_start, block_end)
        
        # now add all the special highlighting
        self.dte.highlight_pattern(r'^\*+\s*(Test Cases?|(User\s+)?Keywords?|Settings?|Variables?)\s*\**', 
                                   "heading", block_start, block_end, whole_lines = True)
        self.dte.highlight_pattern(r'\$\{.*?\}', "variable", block_start, block_end)
        self.dte.highlight_pattern(r'^\s*\*+[^\*]+\*+\s*$', "bold", block_start, block_end)
        self.dte.highlight_pattern(r'^\s*#[^\n]*?$', "comment", block_start, block_end)
        self.dte.highlight_pattern(r'\|\s+#[^\n]*?$', "comment", block_start, block_end)
        self.dte.highlight_pattern('\|', "column_marker", block_start, block_end)
        self.dte.highlight_pattern(" \.\.\. ", "ellipsis", block_start, block_end)

        # only do this for test cases
        # TODO: make sure we only do this in a test case table. ie: don't
        # mark things with "name" if they are in the settings table.
        name_pattern = r'^\|\s+[^\|\s][^\n]*?$'
        for (start, end) in self.get_table_regions("test cases"):
            self.dte.highlight_pattern(name_pattern, "name", start, end)

        # ... and keywords
        for (start, end) in self.get_table_regions("keywords"):
            self.dte.highlight_pattern(name_pattern, "name", start, end)
        
        number_of_lines = int(float(self.dte.index("end")))-1
#        self.dte.tag_configure("cell", background="#f0f8ff")
        self.dte.tag_configure("cell", background="pink")
        start_line = int(float(block_start))
        end_line = int(float(block_end))
        self.linenumbers.update_linenumbers()

        self.event_generate("<<FileChanged>>", data="this is bogus")
