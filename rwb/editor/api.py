import sys
class EditorAPI(object):
    def __init__(self):
        self._save_settings_job = None
        self._tools = []

    def add_tool(self, tool_class):
        self._tools.append(tool_class(self))

    def get_current_editor(self):
        page = self.notebook.get_current_page()
        if page is None:
            return None
        return page.get_text_widget()

    def get_setting(self, key, default=None):
        '''Return a setting for the given key

        A key is expressed in dot notation (eg: editor.foo.bar)
        '''
        section = self.settings
        keys = key.split(".")
        for key in key.split(".")[:-1]:
            section = section.get(key, {})
        return section.get(keys[-1], default)

    def status_message(self, string):
        self.statusbar.message(string)
        
    def set_setting(self, key, value):
        '''Set a setting for the given key

        A key is expressed in dot notation (eg: "editor.recent files")

        FIXME: I think this is busted. I tried setting "editor.foo.bar" 
        and got an error :-(
        '''
        section = self.settings
        keys = key.split(".")
        for key in key.split(".")[:-1]:
            section = section.setdefault(key, {})
        section[keys[-1]] = value
        self.save_settings()
        return section.get(keys[-1], None)

    def save_settings(self, now=False):
        '''Saves all settings; may delay unless now=True
        
        Because of the delay, it's safe to call this on every keypress
        in a preferences panel if you so wish. Each time this is called
        the timer is reset, which means there shouldn't be a performance
        hit while the user is actively typing -- it will save whenever
        the user takes a break.
        '''
        delay = 3000
        if now:
            self.log.debug("writing settings to disk")
            self.settings.write()
            if self._save_settings_job is not None:
                self.after_cancel(self._save_settings_job)
        else:
            if self._save_settings_job is not None:
                self.after_cancel(self._save_settings_job)
            self.after(3000, self.save_settings, True)


