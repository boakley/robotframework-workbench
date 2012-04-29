from robot.parsing.txtreader import TxtReader
import re

class AbstractFilter(object):
    '''Parent class for all filters

    This has methods that are common to all filters, such
    as getting the currently selected text, etc.
    '''
    def __init__(self, app):
        self.app = app
        app.tools_menu.add_command(label=self.label, command=self._apply_filter)

    def filter(self, widget):
        '''Called to apply the filter to the selected text'''
        pass

    def update(self, widget):
        '''Called when the menu item needs to be enabled or disabled
        
        Subclasses can override if they need something fancy; this just
        enables or disables the item based on whether anything is selected
        or not.
        '''
        sel = widget.tag_ranges("sel")
        if len(sel) > 0:
            self.app.tools_menu.entryconfigure(self.label, state="normal")
        else:
            self.app.tools_menu.entryconfigure(self.label, state="disabled")

    def replace_selected_rows(self, rows):
        widget = self.app.get_current_editor()
        string = self.convert_to_string(rows)
        widget.mark_set("sel_start", "sel.first linestart")
        widget.mark_set("sel_end", "sel.last lineend")
        widget.mark_gravity("sel_start", "left")
        widget.mark_gravity("sel_end", "right")
        sel = (widget.index("sel.first linestart"), 
               widget.index("sel.last lineend"))
        widget.replace("sel.first linestart", "sel.last lineend", string)
        widget.tag_add("sel", "sel_start", "sel_end")
        widget.mark_unset("sel_start")

    def get_selected_rows(self):
        '''Return all of the data for all lines that contain the selection

        The data is returned as a list of lists
        '''
        widget = self.app.get_current_editor()
        text = widget.get("sel.first linestart", "sel.last lineend+1c")
        return self._parse_txt(text)

    def convert_to_string(self, rows):
        '''Convert a list of lists into newline-separated, pipe-delimited strings'''
        lines = []
        for row in rows:
            data = "|" + " | ".join(row)
            lines.append(data)
        return "\n".join(lines)
        
    def _apply_filter(self):
        '''Call the filter method with the current text widget'''
        widget = self.app.get_current_editor()
        try:
            self.filter(widget)
        except Exception, e:
            message = "there was a problem applying the filter '%s': %s" % (self.label, str(e))
            self.app.log.warning(message)

    def _parse_txt(self, data):
        '''Parse pipe-separated, plain text robot data
        '''
        lines = data.strip().split("\n")
        if hasattr(TxtReader, "split_row"):
            splitter = TxtReader.split_row
        else:
            splitter = self._split_row
        rows = [[cell.strip() for cell in splitter(row)] for row in lines]
        return rows

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

