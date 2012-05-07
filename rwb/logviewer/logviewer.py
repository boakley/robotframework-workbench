'''
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
from logobjects import RobotLog

class LogTree(ttk.Frame):
    def __init__(self, *args, **kwargs):
        ttk.Frame.__init__(self, *args, **kwargs)

        self.tree = ttk.Treeview(self, columns=("starttime", "endtime"), 
                                 displaycolumns="")
        self.tree.pack(side="top", fill="both", expand=True)

        self.tree.heading("starttime", text="Start Time")
        self.tree.heading("endtime", text="End Time")
        self.tree.column("starttime", width=100, stretch=False)
        self.tree.column("endtime", width=100, stretch=False)

        self.tree.tag_configure("DEBUG", foreground="gray")
        self.tree.tag_configure("TRACE", foreground="gray")
        self.tree.tag_configure("ERROR", background="#FF7e80")
        self.tree.tag_configure("FAIL", foreground="#b22222")
        self.tree.tag_configure("PASS", foreground="#009900")
        self.tree.tag_configure("WARN", background="#ffff00")

    def refresh(self, path=None):
        self.reset()
        if path is not None:
            self.path = path
        for item in self.tree.get_children(""):
            self.tree.delete(item)
        parser = RobotLog()
        parser.parse(self.path)
#            parser.parse(sys.argv[1])

        self.suites = parser.suites
        for suite in self.suites:
            self.after_idle(lambda suite=suite: self._add_suite(suite))

    def reset(self):
        self.suites = []
        for item in self.tree.get_children(""):
            self.tree.delete(item)

    def expand_all(self, node=""):
        self.tree.item(node, open=True)
        for child in self.tree.get_children(node):
            self.expand_all(child)

    def _add_test(self, test, parent_node=None):
        node = self.tree.insert(parent_node, "end", 
                                text=test.name,
                                values=(test.starttime,test.endtime),
                                open=True,
                                tags=("test",test.status))
        for kw in test.keywords:
            self._add_keyword(kw, parent_node=node)

    def _add_keyword(self, kw, parent_node=None):
        text = " | ".join([kw.name] + kw.args)
        kw_node = self.tree.insert(parent_node, "end", 
                                   text=text,
                                   values=(kw.starttime,kw.endtime),
                                   open=True,
                                   tags=("keyword",kw.status))

        # I think instead of doing sub-keywords and then messages,
        # I probably need to process children in order.
        for child_kw in kw.keywords:
            self._add_keyword(child_kw, parent_node=kw_node)

        for msg in kw.messages:
            self.tree.insert(kw_node, "end",
                             text="=> " + msg.text,
                             values=(msg.starttime, msg.endtime),
                             open=False,
                             tags=("message", msg.level))
                
            
    def _add_suite(self, suite, parent_node=""):
        tags=("foo",)
        node = self.tree.insert(parent_node, "end", 
                                text=suite.name,
                                values=(suite.starttime,suite.endtime),
                                open=True,
                                tags=("suite", suite.status))

        if hasattr(suite, "suites"):
            for child_suite in suite.suites:
                self.after_idle(lambda suite=child_suite: self._add_suite(suite, parent_node=node))

        if hasattr(suite, "tests"):
            # for performance reasons, only auto-open test suite directories
            if len([x for x in suite.tests]) > 0:
                self.tree.item(node, open=False)
            for test in suite.tests:
                self.after_idle(lambda test=test: self._add_test(test, parent_node=node))
            
