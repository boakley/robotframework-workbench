import sys
class EditorAPI(object):
    def __init__(self):
        self._save_settings_job = None
        self._tools = []

    def add_tool(self, tool_class):
        self._tools.append(tool_class(self))

    def get_current_editor_page(self):
        page = self.notebook.get_current_page()
        return page

    def get_current_editor(self):
        page = self.notebook.get_current_page()
        if page is None:
            return None
        return page.get_text_widget()

    def status_message(self, string):
        self.statusbar.message(string)
        

