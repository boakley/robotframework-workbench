import Tkinter as tk
import ttk

class RobotLog(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.tree = ttk.Treeview(self)
        vsb = AutoScrollbar(self, command=self.tree.yview, orient="vertical")
        hsb = AutoScrollbar(self, command=self.tree.xview, orient="horizontal")
        self.tree.configure(xscrollcommand=hsb.set, yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tree.tag_configure("FAIL", foreground="#b22222")
        self.tree.tag_configure("PASS", foreground="#009900")
        self.tree.tag_configure("WARN", foreground="#663300")
        self._nodes = [""]

    def _start_process(self, event_id, string):
        parent = self._nodes[-1]
        node = self.tree.insert(parent, "end", text=string, open=True)
        self._nodes.append(node)
        
    def _start_suite(self, event_id,name, attrs):
        parent = self._nodes[-1]
        node = self.tree.insert(parent, "end", text="SUITE %s" % name, open=True)
        self._nodes.append(node)

    def _end_suite(self, event_id, *args):
        node = self._nodes.pop()

    def _start_test(self, event_id, name, attrs):
        parent = self._nodes[-1]
        node = self.tree.insert(parent, "end", text="TEST: %s" % name, open=False)
        self._nodes.append(node)

    def _end_test(self, event_id,name, attrs):
        node = self._nodes.pop()
        self.tree.item(node, tags=(attrs["status"]))

    def _start_keyword(self, event_id, name, attrs):
        parent = self._nodes[-1]
        string = "KEYWORD %s" % (" | ".join([name] + attrs["args"]))
        node = self.tree.insert(parent, "end", text=string, open=False)
        self._nodes.append(node)

    def _end_keyword(self, event_id, name, attrs):
        node = self._nodes.pop()
        if attrs["status"] == "FAIL":
            self.tree.item(node, tags=("FAIL"))
            while node != "":
                parent = self.tree.parent(node)
                self.tree.item(parent, open=True)
                node = parent
        else:
            self.tree.item(node, tags=("PASS"))

    def _log_message(self, event_id, attrs):
        parent = self._nodes[-1]
        if attrs["level"] in ("INFO","WARN","ERROR"):
            string = "%s: %s" % (attrs["level"], attrs["message"].replace("\n", "\\n"))
            node = self.tree.insert(parent, "end", text=string, open=False)

    def _message(self, event_id, message):
        pass
    def _output_file(self, event_id, path):
        pass
    def _log_file(self, event_id, path):
        pass
    def _report_file(self, event_id, path):
        pass
    def _debug_file(self, event_id, path):
        pass
    def _close(self, *args):
        pass
    def _pid(self, event_id, *args):
        print "pid:", args
        pass

    def reset(self):
        self._nodes = [""]
        for item in self.tree.get_children(""):
            self.tree.delete(item)

    def add(self, event_id, method, *args):
        map = {"start_suite":   self._start_suite,
               "end_suite":     self._end_suite,
               "start_test":    self._start_test,
               "end_test":      self._end_test,
               "start_keyword": self._start_keyword,
               "end_keyword":   self._end_keyword,
               "log_message":   self._log_message,
               "message":       self._message,
               "output_file":   self._output_file,
               "log_file":      self._log_file,
               "report_file":   self._report_file,
               "debug_file":    self._debug_file,
               "close":         self._close,
               "pid":           self._pid,
               "start_process": self._start_process,
               }
        func = map[method]
        func(event_id, *args)
        
class old_RobotLog(tk.Frame):

    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.text = tk.Text(self, width=80, borderwidth=0, highlightthickness=0)
        vsb = AutoScrollbar(self, command=self.text.yview, orient="vertical")
        hsb = AutoScrollbar(self, command=self.text.xview, orient="horizontal")
        self.text.configure(xscrollcommand=hsb.set,yscrollcommand=vsb.set)
        self.text.tag_configure("INFO", foreground="#b22222")
        self.text.tag_configure("DEBUG", foreground="gray")
        self.text.tag_configure("WARN", background="yellow")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.text.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def add(self, method, *args):
        if method == "end_keyword" and args[0] == "Teardown":
            tag = "WARN"
        else:
            tag = "INFO"
        self.text.insert("end"," /%s/ " % method, (tag,), ", ".join([str(x) for x in args]), (), "\n")
        self.text.see("end")
#        if method == "end_test":
#            name = args[0]
#            info = args[1]
#            self.text.insert("end", "%8s %s\n" % (info["status"], name))

class AutoScrollbar(ttk.Scrollbar):
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter...
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        ttk.Scrollbar.set(self, lo, hi)
