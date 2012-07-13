from rwb.editor.extensions import AbstractFilter

def __extend__(app):
    app.add_tool(CreateKeyword)
#    app.add_tool(SelectSimilarRows)
#    app.add_tool(AlignColumnsFilter)
#    app.add_tool(CompressColumnsFilter)
    
'''
For the wiki page:

To create an item on the Tools menu, create a class that inherits
from rwb.editor.extensions.AbstractFilter. The class must have
an attribute named 'label' that defines the text that is to appear
on the menu.

When the menu item is selected, it will call the 'filter' method
of the class instance. 

If there is nothing selected in the current widget, the menu item
will be disabled. 
'''

class CreateKeyword(AbstractFilter):
    label = "Convert selection to keyword"
    def filter(self, widget):
        editor_page = self.app.get_current_editor_page()
        print "editor:", editor_page
        print "widget:", widget
        # need to prompt for new name
        name = "New Keyword"
        rows = editor_page.get_selected_rows()
        print rows
        import sys; sys.stdout.flush()
        editor_page.add_keyword(name, rows)
        regions = editor_page.get_table_regions("Keywords")
        print "regions:", regions
#        if len(regions) == 0:
            # need to create a keyword table
#            editor_page.

class SelectSimilarRows(AbstractFilter):
    label = "Select similar rows"
    def filter(self, widget):
        linenumber = widget.index("insert").split(".")[0]
        rows = widget.find_like_rows(linenumber)
        widget.tag_add("sel", "%s.0" % rows[0], "%s.0 lineend" % rows[-1])

    def update(self, widget):
        # always enabled; it doesn't need the selection
        self.app.tools_menu.entryconfigure(self.label, state="normal")

class CompressColumnsFilter(AbstractFilter):
    ''' Trim each cell of extra whitespace'''
    label = "Compress columns"
    def filter(self, widget):
        '''Remove all leading and trailing whitespace from each cell'''
        linenumber = widget.index("insert").split(".")[0]
        rows = widget.find_like_rows(linenumber)
        widget.tag_add("sel", "%s.0" % rows[0], "%s.0 lineend" % rows[-1])

        rows = self.get_selected_rows()
        result = []
        for row in rows:
            row = [cell.strip() for cell in row]
            result.append(row)
        self.replace_selected_rows(result)

    def update(self, widget):
        # always enabled; it doesn't need the selection
        self.app.tools_menu.entryconfigure(self.label, state="normal")

class AlignColumnsFilter(AbstractFilter):
    '''Pad all cells to the same width in each column'''
    label = "Align columns"
    def filter(self, widget):

        linenumber = widget.index("insert").split(".")[0]
        rownums = widget.find_like_rows(linenumber)
        widget.tag_add("sel", "%s.0" % rownums[0], "%s.0 lineend" % rownums[-1])

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

    def update(self, widget):
        # always enabled; it doesn't need the selection
        self.app.tools_menu.entryconfigure(self.label, state="normal")
