import Tkinter as tk
from rwb.widgets import DynamicTableEditor

class RobotDTE(DynamicTableEditor):
    def find_start_of_statement(self, index="insert"):
        '''Find the beginning of the statement that contains the given index

        "Beginning of the statement" is defined as a line that begins
        with "| | " and doesn't contain "..." in the first cell

        '''
        
        mark = "statement_start"
        self.mark_set(mark, "%s linestart" % index)
#        while (self._is_continuation(mark)):
        while (self.compare(mark, ">", "1.0") and 
               self.get(mark, "%s lineend" % mark).startswith("| | ... | ")):
            self.mark_set(mark, "%s-1c linestart" % mark)
        return self.index(mark)
        

    def find_end_of_statement(self, index="insert"):
        '''Find the end of the statement that contains the given index

        "End of the statement" is defined as the beginning of the statement,
        or the last line that follows that is a continuation statement.

        This is highly inaccurate, but Good Enough for now. It doesn't handle
        embedded comments, mainly because I'm too pressed for time right now
        to get the logic right.

        '''
        mark = "statement_start"
        self.mark_set(mark, "%s lineend" % index)
        while (self.compare(mark, "<", "end") and 
               self.get("%s+1c linestart" % mark, "%s+1c lineend" % mark).startswith("| | ... | ")):
            self.mark_set(mark, "%s+1c lineend" % mark)
        return self.index(mark)


