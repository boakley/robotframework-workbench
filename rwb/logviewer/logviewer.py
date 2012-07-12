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
import sys
from rwb.images import data as icons

class LogTree(ttk.Frame):
    def __init__(self, parent, fail_only=False, condensed=False):
        ttk.Frame.__init__(self, parent)

        self.condensed = condensed
        self.fail_only = fail_only
        self.tree = ttk.Treeview(self, columns=("starttime", "endtime", "feh"), 
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
#        self.tree.tag_configure("PASS", foreground="#009900")
        self.tree.tag_configure("WARN", background="#ffff00")
        # FIXME: need to get this from the app object somehow,
        # or it needs to be passed in.
        self.tree.tag_configure("message", font="TkFixedFont")

        self._failures = []
        self._init_images()

    def _init_images(self):
        self._image = {
            "suite": tk.PhotoImage(data=icons["table_multiple"]),
            "test":  tk.PhotoImage(data=icons["table"]),
            "keyword": tk.PhotoImage(data=icons["cog"]),
            }

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

    def expand_suites(self, node=""):
        '''Expand only the root and suites that have other suites

        The goal is to make all suites visible, everything else not.
        '''
        self.tree.item(node, open=True)
        for child in self.tree.get_children(node):
            self.expand_all(child)

        
    def expand_all(self, node=""):
        self.tree.item(node, open=True)
        for child in self.tree.get_children(node):
            self.expand_all(child)

    def _add_suite(self, suite, parent_node=""):
        if self.fail_only and not suite.failed:
            return

        node = self.tree.insert(parent_node, "end", 
                                text=suite.name,
                                image=self._image["suite"],
                                values=(suite.starttime,suite.endtime,suite),
                                open=True,
                                tags=("suite", suite.status))

        for kw in suite.keywords:
            self._add_keyword(kw, parent_node=node)

        if hasattr(suite, "suites"):
            for child_suite in suite.suites:
                self.after_idle(lambda suite=child_suite: self._add_suite(suite, parent_node=node))

        if hasattr(suite, "tests"):
            # for performance reasons, only auto-open test suite directories,
            # unless we're in "fail only" mode
            if len([x for x in suite.tests]) > 0:
                self.tree.item(node, open=self.fail_only)
            for test in suite.tests:
                self.after_idle(lambda test=test: self._add_test(test, parent_node=node))
            
    def _add_test(self, test, parent_node=None):
        if self.fail_only and not test.failed:
            # I should use proper logging...
            print "skipping; status is", test.status
            return

        node = self.tree.insert(parent_node, "end", 
                                text=test.name,
                                values=(test.starttime,test.endtime, test),
                                image=self._image["test"],
                                open=False,
                                tags=("test",test.status))
        for kw in test.keywords:
            self._add_keyword(kw, parent_node=node)

    def _add_keyword(self, kw, parent_node=None):
#        name = kw.name.rsplit(".",1)[-1]
        text = " | ".join([kw.shortname] + kw.args)
        kw_node = self.tree.insert(parent_node, "end", 
                                   text=text,
                                   values=(kw.starttime,kw.endtime, kw),
                                   image=self._image["keyword"],
                                   open=False,
                                   tags=("keyword",kw.status))

        if kw.status == "FAIL":
            # make sure all ancestors are open
            self.tree.item(kw_node, open=True)
            parent = self.tree.parent(kw_node)
            while parent != "":
                self.tree.item(parent, open=True)
                parent = self.tree.parent(parent)

            self._failures.append(kw_node)

        # I think instead of doing sub-keywords and then messages,
        # I probably need to process children in order.
        for child_kw in kw.keywords:
            self._add_keyword(child_kw, parent_node=kw_node)

        for msg in kw.messages:
            lines = msg.text.split("\n")
            for line in lines:
                self.tree.insert(kw_node, "end",
                                 text=line,
                                 values=(msg.starttime, msg.endtime, msg),
                                 open=False,
                                 tags=("message", msg.level))
            
    def previous_with_tag(self, *tags):
        '''Find previous item with the given tags
        '''
        item = self._previous_element()
        tagset = set(tags)
        while item != "" and not tagset.issubset(set(self.tree.item(item, "tags"))):
            item = self._previous_element(item)
        return item

    def next_with_tag(self, *tags):
        '''Find next item with the given tags

        For example, to find the next failing keyword do something like:
        tree.next_with_tag("keyword","FAIL")
        '''
        item = self._next_element()
        tagset = set(tags)
        while item != "" and not tagset.issubset(set(self.tree.item(item, "tags"))):
            item = self._next_element(item)
        return item
        
    def _previous_element(self, element=None):
        '''Return the previous element, whether it's visible or not'''
        if element is None:
            selection = self.tree.selection()
            if len(selection) > 0:
                item = selection[-1]
            else:
                item = ""
        else:
            item = element
        
        previous = self.tree.prev(item)
        if previous == "":
            return self.tree.parent(item)

        # there is a previous element; we need to drill down
        # to find the bottom-most leaf node in that previous
        # element's hierarchy
        node = previous
        while len(self.tree.get_children(node)) > 0:
            node = self.tree.get_children(node)[-1]
        return node


    def _next_element(self, element=None):
        '''Return the next element, whether it's visible or not'''
        if element is None:
            selection = self.tree.selection()
            if len(selection) > 0:
                item = selection[-1]
            else:
                item = ""
        else:
            item = element
        children = self.tree.get_children(item)
        if len(children) > 0:
            return children[0]

        up = self.tree.parent(item)
        down = self.tree.next(up)
        while up != "" and down == "":
            up = self.tree.parent(up)
            down = self.tree.next(up)

        return down

        
