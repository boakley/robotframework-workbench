import Tkinter as tk
from robot.parsing.txtreader import TxtReader
import ttk
import sys
import re
from rwb.widgets import HighlightMixin
import logging
#from core.transmogrifier import Transmogrifier

import tcl

'''
widget = ".%s" % self.text.winfo_name()
# ugh! my head hurts! My eyes! The goggles do nothing!  find all
# instances of a pipe either at the beginning of a line or after
# a space, and followed by a space or end of line. Thank goodness
# robot requires spaces on either side of the pipe, that makes
# parsing much easier. 
cmd = r'%s search -all -regexp {(^| )\|( |$)} 1.0 {1.0 lineend}' % widget
result = self.tk.eval(cmd).split(" ")
print "result:", result
print tk.__file__

'''

# decorator which can be added to a method
def timeit(func):
    import time
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print '%s took %0.3f ms' % (func.func_name, (t2-t1)*1000.0)
        import sys; sys.stdout.flush()
        return res
    return wrapper

class DynamicTableEditor(tk.Text, HighlightMixin):
    '''A text widget with some magic for managing columns of data separated with pipes'''
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)
        font = self.cget("font")
        self.log = logging.getLogger("dte")

        self.tmpvar = tk.IntVar(master=self, name="::__countx__")

        # add a special bind tag before the class binding so we can
        # preempt the default bindings when the completion window is
        # visible (eg: up and down arrows will affect the selection in
        # the dropdown list rather than the cursor position)
        bindtags = self.bindtags()
        new_bindtags = tuple([bindtags[0], "Completion"] + list(bindtags[1:]))
        self.bindtags(new_bindtags)
        self.bind_class("Completion","<Control-space>", self._on_autocomplete)
        self.bind_class("Completion","<Escape>", self._on_escape)
        self.bind_class("Completion","<Key-Down>", self._on_down)
        self.bind_class("Completion","<Key-Up>", self._on_up)
        self.bind_class("Completion","<Any-Key-Return>", self._on_return)
        self.bind_class("Completion","<Tab>", self._on_tab)
        self.bind_class("Completion","<1>", self._on_click)
        self.bind("<Control-w>", self._on_select_block)

        # should these be in the caller? They are robot-specific
        # but my long term goal is for this widget to be somewhat
        # generic
        self.bind("<{>", self._on_brace_open)
        self.bind("<|>", self._on_pipe)
        self.bind("<Tab>", self.on_tab)
        self.bind("<Triple-1>", self._on_triple_click) 
        self.bind("<Control-Return>", self._on_control_enter)
        self.bind("<Control-\\>", self._on_expand)
        self.bind("<<Paste>>", self._on_paste)
        
        # other ideas:
        # double-1: if inside a variable, select only the word not the
        # whole cell
        # return or tab: if in table name (ie, inbetween *** and ***), move
        # to the next line

        self.tag_configure("current_line", background="#f2f2f2")

        # since we automatically add a space after an inserted pipe,
        # we want to ignore a space that immediately follows since
        # it's easy to think "I need a pipe and a space". Without this
        # you would end up with two spaces, negating any gain from
        # automatically adding one
        self.bind("<|><space>", lambda event: "break")

        # this stuff is related to auto-complete
        self.complete_frame = ttk.Frame(self)
        self.list = tk.Listbox(self.complete_frame, width=30, height=8, 
                               borderwidth=1, relief="solid", exportselection=False)
        self.list.pack(side="top", fill="both", expand=True)
        self.hooks = []

        post_change_hook = self.register(self._post_change_hook)
        widget = str(self)
        self.tk.eval(tcl.CREATE_WIDGET_PROXY)
        self.tk.eval('''
            rename {widget} _{widget}
            interp alias {{}} ::{widget} {{}} widget_proxy _{widget} {post_change_hook}
        '''.format(widget=widget, post_change_hook=post_change_hook))
        self._last_current_cell_start = ""

    def set_completion_choices(self, choices):
        self.list.delete(0, "end")
        for string in choices:
            self.list.insert("end", string)
        self.list.selection_set(0)
        self._reposition_choices()
        self.list.configure(height=min(len(choices), 10))

    def get_autocomplete_string(self):
        try:
            return self.get("current_cell.first", "current_cell.last")
        except:
            return "WTF?"

    def select_similar_rows(self, index="insert"):
        linenum = int(self.index("insert").split(".")[0])
        rows = self.find_like_rows(linenum)
        self.tag_remove("sel", 1.0, "end")
        self.tag_add("sel", "%s.0" % rows[0], "%s.0 lineend" % rows[-1])

    def get_selected_rows(self):
        '''Return all of the data for all lines that contain the selection

        The data is returned as a list of lists
        '''
        try:
            first_linenum = int(self.index("sel.first").split(".")[0])
            last_linenum = int(self.index("sel.last").split(".")[0])
            result = [self.get_row(linenum) for linenum in range(first_linenum, last_linenum+1)]
        except Exception, e:
            self.log.debug(str(e))
            result = []
        return result

    def compress_rows(self, anchor="insert"):
        linenumber = self.index(anchor).split(".")[0]
        rows = self.find_like_rows(linenumber)
        self.tag_add("sel", "%s.0" % rows[0], "%s.0 lineend" % rows[-1])

        rows = self.get_selected_rows()
        result = []
        for row in rows:
            row = [cell.strip() for cell in row]
            result.append(row)
        self.replace_selected_rows(result)

    def align_rows(self, anchor="insert"):
        self.select_similar_rows(anchor)

        rows = self.get_selected_rows()
        col_size = {}
        for row in rows:
            for i, col in enumerate(row):
                col_size[i] = max(col_size.get(i, 0), len(col))
        ncols = len(col_size)
        result = []
        for row in rows:
            row = list(row) + [''] * (ncols - len(row))
            for i, col in enumerate(row):
                row[i] = col.ljust(col_size[i])
            result.append(row)
        self.replace_selected_rows(result)

    def convert_to_string(self, rows):
        '''Convert a list of lists into newline-separated, pipe-delimited strings
        Is this a dupe of another function somewhere? *sigh* I need to clean this
        API up!
        '''
        lines = []
        for row in rows:
            data = "| " + " | ".join(row)
            lines.append(data.rstrip())
        return "\n".join(lines)

    def replace_selected_rows(self, rows):
        string = self.convert_to_string(rows)
        self.mark_set("sel_start", "sel.first linestart")
        self.mark_set("sel_end", "sel.last lineend")
        self.mark_gravity("sel_start", "left")
        self.mark_gravity("sel_end", "right")
        sel = (self.index("sel.first linestart"), 
               self.index("sel.last lineend"))
        self.replace("sel.first linestart", "sel.last lineend", string)
        self.tag_add("sel", "sel_start", "sel_end")
        self.mark_unset("sel_start")
        
    def find_like_rows(self, linenumber):
        '''Remarkably, this is pretty fast. About 1ms the last time I timed it

        Admittedly, the algorithm is pretty clunky and could stand for some optimization
        '''
        start = end = anchor = int(linenumber)
        row = self.get_row(linenumber)
        if len(row) == 1 and row[0] == "":
            self.tag_remove("like", "1.0", "end")
            self.tag_add("like", "%s.0 linestart" % linenumber, "%s.0 lineend+1c" % linenumber)
            return (anchor,)
        required_rows = len(row)
        for linenumber in range(anchor-1, 0, -1):
            row = self.get_row(linenumber)
            if len(row) != required_rows or (len(row) == 1 and row[0] == ""):
                break
            start = linenumber

        lastline = int(self.index("end").split(".")[0])
        for linenumber in range(anchor+1, lastline):
            row = self.get_row(linenumber)
            if len(row) != required_rows or (len(row) == 1 and row[0] == ""):
                break
            end = linenumber

        self.tag_remove("like", "1.0", "end")
        self.tag_add("like", "%s.0 linestart" % start, "%s.0 lineend+1c" % end)
        return range(start, end+1)
    
    def get_rows(self, rownums):
        result = []
        for rownum in rownums:
            result.append(self.get_row(rownum))
        return result

    def get_row(self, linenumber):
        '''Return a row as a list of values

        This replicates the functionality of robot.parsing.txtreader.split_row
        in robot 2.7 (which isn't officially out yet...)
        '''

        line_start = "%s.0" % linenumber
        line_end = self.index(line_start + " lineend")
        text = self.get(line_start, line_end).strip()
        return self._split_row(text)
#        pipe_splitter = re.compile(' \|(?= )')
#        if text.endswith(' |'):
#            text = text[1:-1]
#        return [x.strip() for x in pipe_splitter.split(text)]

    def _split_row(self, row):
        '''This exists for backwards compatibility with rf 2.6 and older
        
        Prior to robot framework 2.7a2, the method for
        splitting rows was private. This is a cut'n'paste
        from the 2.7a2 sources.
        '''
        _space_splitter = re.compile(' {2,}')
        _pipe_splitter = re.compile(' \|(?= )')

        row = row.rstrip().replace('\t', '  ')
        if not row.startswith('| '):
            return _space_splitter.split(row)
        row = row[1:-1] if row.endswith(' |') else row[1:]
        return [cell.strip() for cell in _pipe_splitter.split(row)]

    def current_cell(self):
        '''Return the boundaries of the current cell'''
        (start, end) = self._current_cell_boundaries()
        return (start, end)

    def select_current_cell(self):
      ''' Whadya know? This seems to work'''
      (start, end) = self._current_cell_boundaries()
      self.tag_remove("sel", 1.0, "end")
      self.tag_add("sel", start, end)

    def move_to_next_column(self):
        if self.complete_frame.winfo_viewable():
            self.complete_frame.place_forget()

        i = self.search("(^| )\|( |$)", "insert", regexp=True, count=self.tmpvar)
        if (i != ""):
            self.mark_set("insert", "%s+%sc" % (i, self.tmpvar.get()))
            # special case for empty cells
            if (self.get("insert") == "|"):
                self.mark_set("insert", "insert-1c")
            self.select_current_cell()
            self.see("insert")

    def add_post_change_hook(self, cmd):
        '''Register a command to be called whenever the data changes'''
        self.hooks.append(cmd)

    def replace(self, start, end, string, tags=None):
        '''Replace a range of text'''
        insert = self.index(start)
        self.configure(autoseparators=False)
        self.edit_separator()
        self.delete(start, end)
        self.insert(insert, string, tags)
        self.edit_separator()
        self.configure(autoseparators=True)
    
    def _on_paste(self, event):
        '''I was having problems on my mac where the clipboard had 
        strings terminated by \r. This converts those to newlines
        before doing the paste
        '''
        data = self.clipboard_get().replace("\r\n", "\n").replace("\r", "\n")
        self.edit_separator()
        try:
            self.delete("sel.first", "sel.last")
        except:
            pass
        self.insert("insert", data)
        self.edit_separator()
        return "break"

    def _on_expand(self, event):
        sys.stdout.flush()
        
    def _on_select_block(self, event):
        '''Select a block of text (not fully implemented yet!)
        
        The idea is that subsequent calls escalate from selecting the
        variable, cell, line, block, and whole test case, or something like
        that.

        How shall I implement this? I could bind to <Control-w>, 
        <Control-w><Control-w>, <Control-w><Control-w><Control-w>, etc
        or I could somehow determine what is selected and go the next
        one bigger. The former is easy, but
        '''
        sel = self.tag_ranges("sel")
        if len(sel) == 0:
            # no selection; select current cell
            self.select_current_cell()
        else:
            # there is a selection; select current cell if it's
            # not selected, select row if it is. 
            self.select_current_cell()
            if self.tag_ranges("sel") == sel:
                # it was already selected; select whole line instead
                self.tag_add("sel", "insert linestart", "insert lineend")

    def _on_control_enter(self, event):
        '''Enter a newline, and indent appropriately
        
        Useful when entering rows for a text, so you don't
        have to manually type so many pipes
        '''
        line = self.get("insert linestart", "insert lineend")
        match = re.match(r'[ |.]*', line)
        if match:
            self.insert("insert", "\n" + match.group(0))
            if re.match(r'[ |.]*\| +:[Ff][Oo][Rr] +', line):
                # line is a FOR loop; add one more level of indentation
                self.insert("insert", "| ")
            return "break"

    def _on_triple_click(self, event):
      print "on_triple_click..."
      self.select_current_cell()
      return "break"

    def on_tab(self, event):
        '''Special handling for the tab key
        
        Lots of things are going on here. We might move to the next
        cell, or we add indentation based on the previous line, or add
        a new column to the current row.
        '''
        if self.complete_frame.winfo_viewable():
            self.complete_frame.place_forget()

        # are we in a variable? If so, move to just outside the variable
        line = self.get("insert linestart", "insert")
        if re.search(r'\${[^}]*$', line):
            index = self.search("} *", "insert", regexp=True,
                                stopindex="insert lineend", count=self.tmpvar)
            if index != "":
                self.mark_set("insert", "%s+%sc" % (index, self.tmpvar.get()))
                return "break"

        # are we at the beginning of a blank line? If so, add indentation
        # equal to the previous line
        if (self.compare("insert",">","1.0") and
            self.compare("insert", "==", "insert linestart")  and
            self.compare("insert", "==", "insert lineend")):
            previous_line = self.get("insert -1 line linestart", "insert -1 line lineend")
            match = re.match(r'^([ |.]+)', previous_line)
            if match:
                self.insert("insert", match.group(1))
                return "break"

        # Or, we might want to add a new column based
        if self._should_add_new_column():
            self.insert("insert", " | ")
            return "break"
        else:
            self.move_to_next_column()
        return "break"

    def _current_cell_boundaries(self):

        # find the separator prior to this cell
        i = self.search("(^| )\|( |$)", "insert", regexp=True, 
                        count=self.tmpvar, backwards=True,
                        stopindex="insert linestart")
        if i == "":
            start = self.index("insert linestart")
        else:
            start = self.index("%s+%sc" % (i, self.tmpvar.get()))
        i = self.search(" \|( |$)", "insert", stopindex="insert lineend", regexp=True)
        if i == "": i = self.index("insert lineend")
        return (start, i)

    def _should_add_new_column(self):
        if (self.compare("insert", "==", "insert lineend")):
            index = self.search(r'\| +$', "insert", backwards=True, regexp=True, 
                            stopindex="insert linestart")
            if index == "":
                return True
        return False

    def _on_pipe(self, event):
        # if we are preceeded by zero, or an odd number of backslashes,
        # insert a new column separator

        # beginning of line gets special treatment
        if (self.compare("insert", "==", "insert linestart")):
          self.insert("insert", "| ")
          return "break"

        prev = self.get("insert-1c")
        if (prev == "\\"):
            self.insert("insert", "|")
            return "break"

        if (prev != " "):
            self.insert("insert", " ")
        self.insert("insert", "|", "column_marker")
        self.insert("insert", " ")
        return "break"

    def _on_brace_open(self, event):
        # if the prev char is a $, automagically add a close curly
        prev = self.get("insert-1c")
        prevprev = self.get("insert-1c")
        if (prev == "$" and prevprev != "\\"):
            self.insert("insert", "{}")
            self.tag_add("variable", "insert-3c", "insert")
            self.mark_set("insert", "insert-1c")
            self.edit_separator()
            return "break"

    ### auto complete stuff

    def _on_click(self, event):
        try:
            if self.complete_frame.winfo_viewable():
                self.complete_frame.place_forget()
        except:
            pass

    def _post_change_hook(self, result, command, *args):
        self._tag_current_cell()
        self.tag_remove("current_line", 1.0, "end")
        self.tag_add("current_line", "insert linestart", "insert lineend +1c")
        self._reposition_choices()
        for func in self.hooks:
            try:
                func(result, command, *args)
            except Exception, e:
                print "warning: exception in post_change_hook:", e

        if (command in ("insert","delete") and  self.complete_frame.winfo_viewable()):
            self.event_generate("<<AutoComplete>>")
            
        line = self.index("insert").split(".")[0]
        self.find_like_rows(line)

    def _on_any_key(self, event):
        if self.complete_frame.winfo_viewable():
            self.event_generate("<<AutoComplete>>")
            
    def _on_tab(self, event):
        if self.complete_frame.winfo_viewable():
            selection = self.list.curselection()
            if selection is not None and len(selection) > 0:
                i = selection[0]
                text = self.list.get(i)
                self.replace("current_cell.first", "current_cell.last", text)
                self.complete_frame.place_forget()
                self.move_to_next_column()
                return "break"
        self.move_to_next_column()
        return "break"

    def _on_return(self, event):
        try:
            if self.complete_frame.winfo_viewable():
                selection = self.list.curselection()
                if selection is not None and len(selection) > 0:
                    i = selection[0]
                    text = self.list.get(i)
                    self.replace("current_cell.first", "current_cell.last", text)
                    self.complete_frame.place_forget()
                    return "break"
        except:
            pass

    def _select_next(self):
        selection = self.list.curselection()
        if selection is not None and len(selection) > 0:
            index = int(selection[0])+1
            self.list.activate(index)
            self.list.see(index)
            self.list.selection_clear(0, "end")
            self.list.selection_set("active")

    def _select_prev(self):
        selection = self.list.curselection()
        if selection is not None and len(selection) > 0:
            index = int(selection[0])-1
            self.list.activate(index)
            self.list.see(index)
            self.list.selection_clear(0, "end")
            self.list.selection_set("active")

    def _on_up(self, event):
        if self.complete_frame.winfo_viewable():
            self._select_prev()
            return "break"

    def _on_down(self, event):
        if self.complete_frame.winfo_viewable():
            self._select_next()
            return "break"

    def _on_escape(self, event):
        if (self.complete_frame.winfo_viewable()):
            self.complete_frame.place_forget()

    def _tag_current_cell(self):
        self.tag_remove("current_cell", 1.0, "end")
        (start, end) = self.current_cell()
        self.tag_add("current_cell", start, end)
        return
        i = self.search(" \| ", "insert", stopindex="insert linestart", 
                        backwards=True, regexp=True)
        if i == "":
            cell_start = self.index("insert linestart")
        else:
            cell_start = self.search(r'[^\s]', "%s+3c" % i, regexp=True)

        i = self.search(" +\| ", cell_start, stopindex="insert lineend", regexp=True)
        if i == "":
            cell_end = self.index("insert lineend")
        else:
            cell_end = i
        self.tag_remove("current_cell", 1.0, "end")
        self.tag_add("current_cell", cell_start, cell_end)
        
    def _on_autocomplete(self, event):
        self.event_generate("<<AutoComplete>>")
        self._reposition_choices(force=True)

    def _reposition_choices(self, force=False):
        # remove this line to have auto-completion window almost
        # always visible. I can't decide -- automatic, or only
        # on control-space.
        if not force and not self.complete_frame.winfo_viewable():
            return

        try:
            bbox = self.bbox("current_cell.first")
        except Exception, e:
            return
        fx = bbox[0]
        fy = bbox[1] + bbox[3] + 2
        yoffset = 2
        listheight = self.complete_frame.winfo_reqheight()
        if fy+listheight > self.winfo_height():
            # won't fit below; go to plan B!
            fy = bbox[1]-(listheight+ yoffset)
            if fy < 1:
                # crap! won't fit above either. Screw it. Show it
                # below and let the user suffer the consequences.
                fy = bbox[1] + bbox[3] + yoffset
        # print "   fx/fy:", fx,fy
        # print "  height:", self.winfo_height()
        # print "       reqheight of frame:", self.complete_frame.winfo_reqheight()
        # print "   actual height of frame:", self.complete_frame.winfo_height()
        self.complete_frame.place(x=fx, y=fy)

if __name__ == "__main__":
    import sys
    root = tk.Tk()
    dte = DynamicTableEditor(root, highlightthickness=0)
    vsb = tk.Scrollbar(root, orient="vertical", command=dte.yview)
    hsb = tk.Scrollbar(root, orient="horizontal", command=dte.xview)
    dte.configure(xscrollcommand=hsb.set, yscrollcommand=vsb.set)
    dte.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    root.mainloop()
