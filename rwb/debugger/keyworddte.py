import Tkinter as tk
from rwb.widgets import DynamicTableEditor
from rwb.editor import DteMargin

class KeywordDTE(DynamicTableEditor):
    '''A dynamic table editor for entering keywords (versus full test cases)'''

    def __init__(self, *args, **kwargs):
        DynamicTableEditor.__init__(self, *args, **kwargs)
        self.margin = DteMargin(self, width=32, background=self.cget("background"), 
                                borderwidth=0, highlightthickness=0)
        self.margin.attach(self)

    def get_current_statement(self):
        '''Return the current statement as a list of cells

        This doesn't do it exactly like robot does, but we want to be
        a bit forgiving on what the user types in. File this in the
        not-like-robot-does-but-probably-what-the-user-expects category.
        '''
        text = self.get_current_statement_text()
        if not text.lstrip().startswith("|"): text = "| " + text
        lines = text.split("\n")
        statement = self._split_row(lines[0])
        for line in lines[1:]:
            # this is gross. Let's ignore all leading and trailing
            # empty cells, no matter how many there are. Then, we have
            # to make sure the line starts with a pipe so the splitter
            # can work properly. Finally, we'll assume that for the 
            # second and all subsequent lines, the first cell contains
            # "..." and should be ignored.
            #
            # this isn't exactly proper robot parsing, but since this
            # is somewhat of a free-form input field we want to be 
            # forgiving about requiring leading pipes
            #
            line = line.strip(" |")
            line = "| " + line
            row = self._split_row(line)
            statement.extend(row[1:])
        return statement

    def find_start_of_statement(self, index="insert"):
        '''Find the beginning of the statement that contains the given index

        This is highly inaccurate, but Good Enough for now. It will, for
        example, think these three are part of the same statement:
        | one
        | | ... | two
        ... | three

        Like I said, it's good enough for now. It catches all normal
        cases; I can always improve it later. 
        '''
        
        mark = "statement_start"
        self.mark_set(mark, "%s linestart" % index)
        while (self.compare(mark, ">", "1.0") and 
               self.get(mark, "%s lineend" % mark).lstrip("| ").startswith("... | ")):
            self.mark_set(mark, "%s-1c linestart" % mark)
        return self.index(mark)

    def find_end_of_statement(self, index="insert"):
        '''Find the end of the statement that contains the given index

        This is highly inaccurate, but Good Enough for now. It will, for
        example, think these three are part of the same statement:
        | one
        | | ... | two
        ... | three

        Like I said, it's good enough for now. It catches all normal
        cases; I can always improve it later. 
        '''
        mark = "statement_start"
        self.mark_set(mark, "%s lineend" % index)
        while (self.compare(mark, "<", "end") and 
               self.get("%s+1c linestart" % mark, "%s+1c lineend" % mark).lstrip("| ").startswith("...")):
            self.mark_set(mark, "%s+1c lineend" % mark)
        return self.index(mark)
