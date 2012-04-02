'''
Robot Framework Workbench

Copyright (c) 2012 Bryan Oakley

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import Tkinter as tk
import ttk

class SettingsDialog(tk.Toplevel):
    def __init__(self, app):
        self.app = app
        tk.Toplevel.__init__(self, app)
        # we can't associate frame widgets with items in the tree,
        # so we have to build a mapping of class names to instances
        self._frames = {}
        self._create_ui()
        self.refresh()
        self.wm_geometry("700x400")

    def _create_ui(self):
        ttk.Frame(self).place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
        pw = ttk.PanedWindow(self, orient="horizontal")
        self.tree = ttk.Treeview(pw, selectmode="browse", show=("tree",))
        self.container = ttk.Frame(pw)
        button_frame = ttk.Frame(self)
        apply = ttk.Button(self, text="Ok")
        apply.pack(in_=button_frame, side="right")
        button_frame.pack(side="bottom", fill="x", padx=4, pady=4)
        pw.pack(side="top", fill="both", expand=True)
        pw.add(self.tree)
        pw.add(self.container)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def refresh(self):
        '''Danger Will Robinson!
        At the moment this isn't a proper refresh; it doesn't delete
        any existing data
        '''
        for class_ in self.app.get_settings_frames():
            section = class_.section
            parent = ""
            for name in class_.section:
                if name not in [self.tree.item(child, "text") 
                                for child in self.tree.get_children(parent)]:
                    parent = self.tree.insert(parent, "end", text=name, open=True, values=[])
                else:
                    parent = child
            f = class_(self)
            self._frames[str(f)] = f
            self.tree.insert(parent, "end", text=class_.title, values=(str(f),))

    def _on_tree_select(self, event=None):
        selected_item = self.tree.selection()[0]
        if selected_item:
            values = self.tree.item(selected_item, "values")
            if values:
                settings_frame = self._frames[values[0]]
                settings_frame.place(in_=self.container, x=0, y=0, relwidth=1, relheight=1)
                settings_frame.lift()

