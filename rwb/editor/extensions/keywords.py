import Tkinter as tk
def foo(*args):
    print "foo!", args
    import sys; sys.stdout.flush()

def __extend__(app):
    extension = KeywordExtension(app)
    app.bind_class("all", "<F5>", extension.make_keyword)
    # this needs to add something to the tools menu...

class KeywordExtension(object):
    def __init__(self, app):
        self.app = app
        pass

    def make_keyword(self, event=None):
        # N.B. this is the editor_page object
        editor = self.app.get_current_editor()
        
        rows = editor.get_selected_rows()
        print rows
        import sys; sys.stdout.flush()

        # now I want to do something like:
        '''
        editor.delete_selected_rows()
        editor.new_keyword(rows)
          => prompts user for a name (with a 'place'd dialog rather than a popup?
             then creates the keyword with that name, and replaces the selected
             text with a reference to that keyword

        '''
        self.app.status_message("an extension says hello; you have selected %s rows" % len(rows))

