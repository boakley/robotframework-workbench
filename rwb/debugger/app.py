import Tkinter as tk
import ttk
import xmlrpclib
import re
from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from rwb.runner import RobotLogTree, RobotLogMessages
from rwb.lib import AbstractRwbGui
from rwb.widgets import Statusbar
from varlist import VariableList
from rwb.runner.listener import JSONSocketServer

NAME = "debugger"
HELP_URL="https://github.com/boakley/robotframework-workbench/wiki/rwb.debugger-User-Guide"
DEFAULT_SETTINGS = {
    NAME: {
        "port": 8910,
        "host": "localhost",
        "geometry": "1200x600",
        }
    }

class DebuggerApp(AbstractRwbGui):
    def __init__(self):
        import sys; sys.stdout=sys.__stdout__
        AbstractRwbGui.__init__(self, NAME, DEFAULT_SETTINGS)
        port = int(self.get_setting("debugger.port"))
        self.listener = JSONSocketServer(self, port=port, callback=self._listen)
        self.wm_title("rwb." + NAME)
        self._create_menubar()
        self._create_toolbar()
        self._create_statusbar()
        self._create_main()
        self.stack = []
        self.event_id = 0
        self.set_idle_state()
        self.heartbeat()

    def heartbeat(self):
        '''Continually ping remote to see if it is alive

        This, to reset the state in case the remote process
        dies on us or becomes unresponsive.
        '''
        try:
            self.proxy("ping")
        except Exception, e:
            self.set_idle_state()
        self.after(2000, self.heartbeat)
        
    def set_idle_state(self):
        '''Set the app state to idle

        This sets the normal/disabled states of the
        buttons appropriate for the current state
        '''
        self.continue_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")
        self.fail_button.configure(state="disabled")
        self.eval_button.configure(state="disabled")
        self.statusbar.progress_stop()
        self.statusbar.set("state", "idle")

    def set_running_state(self):
        '''Set the app state to running

        This sets the normal/disabled states of the
        buttons appropriate for the current state
        '''
        self.continue_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")
        self.fail_button.configure(state="disabled")
        self.eval_button.configure(state="disabled")
        self.statusbar.progress_start()
        self.statusbar.set("state", "running")

    def set_break_state(self):
        '''Set the app state to break

        This sets the normal/disabled states of the
        buttons appropriate for the current state
        '''
        self.continue_button.configure(state="normal")
        self.stop_button.configure(state="normal")
        self.fail_button.configure(state="normal")
        self.eval_button.configure(state="normal")
        self.statusbar.set("state", "breakpoint")

    def on_exit(self, *args):
        # it can take a second or so for the app to fully exit,
        # so we'll withdraw the window so it appears to die quickly.
        self.wm_withdraw()
        try:
            # in case the remote robot instance is waiting for us,
            # let's send a continue command
            self.proxy("resume")
        except Exception, e:
            self.log.debug("on_exit caught an error: %s" % str(e))
            # I probably should log something...
            pass
        AbstractRwbGui.on_exit(self, *args)
        self.destroy()
        
    def _create_toolbar(self):
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(side="top", fill="x")
        self.continue_button = ttk.Button(self.toolbar,text="->", width=8,
                                          command=lambda: self.proxy("resume"))
        self.stop_button = ttk.Button(self.toolbar, text="stop", width=8,
                                          command=lambda: self.proxy("stop"))
        self.fail_button = ttk.Button(self.toolbar, text="fail test", width=8,
                                          command=lambda: self.proxy("fail"))

        self.eval_button = ttk.Button(self.toolbar, text="eval", command=self._on_eval, width=8)

        self.continue_button.pack(side="left")
        self.stop_button.pack(side="left")
        self.fail_button.pack(side="left")
        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", fill="y", padx=4, pady=2)
        self.eval_button.pack(side="left")

    def refresh_vars(self):
        self.varlist.reset()
        try:
            variables = self.proxy("get_variables")
            for key in sorted(variables.keys(), key=str.lower):
                # for reasons I don't yet understand, backslashes are getting interpreted
                # as escape sequences. WTF?
                try:
                    value = variables[key]
                    value = value.replace("\\", "\\\\")
                except: 
                    pass
                self.varlist.add(key, value)
        except Exception, e:
            print "refresh_vars failed:", e

    def _on_eval(self):
        code = self._split(self.input.get("insert linestart", "insert lineend"))
        print "code:", " | ".join(code)
        
    def proxy(self, command):
        proxy = xmlrpclib.ServerProxy("http://localhost:%s" % self.remote_port,allow_none=True)
        dispatch = {"resume":        proxy.resume,
                    "stop":          proxy.stop,
                    "fail":          proxy.fail,
                    "ping":          proxy.ping,
                    "get_variables": proxy.get_variables,
                    }
        return dispatch[command]()

    def _create_menubar(self):
        self.menubar = tk.Menu(self)
        self.configure(menu=self.menubar)
        self.file_menu = tk.Menu(self.menubar, tearoff=False)
        self.file_menu.add_command(label="Exit", command=self.on_exit)
        self.help_menu = tk.Menu(self.menubar, tearoff=False)
        self.help_menu.add_command(label="View help on the web", command=self._on_view_help)
        self.menubar.add_cascade(menu=self.file_menu, label="File", underline=0)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="About the robotframework workbench", command=self._on_about)
        self.menubar.add_cascade(label="Help", menu=self.help_menu)

    def _on_view_help(self):
        import webbrowser
        webbrowser.open(HELP_URL)
#        page = self.notebook.add_custom_page(page_class=help.HelpPage)

    def _create_statusbar(self):
        self.statusbar = Statusbar(self)
        self.statusbar.pack(side="bottom", fill="x")
        self.statusbar.add_section("port",12, "port %s" % self.listener.port)
        self.statusbar.add_section("state", 12)
        self.statusbar.add_progress(mode="indeterminate")
        # grip = ttk.Sizegrip(self.statusbar)
        # grip.pack(side="right")
        # self.status_label = ttk.Label(self.statusbar, text="", anchor="w")
        # self.status_label.pack(side="left", fill="both", expand="true", padx=8)
        # self.statusbar.pack(side="bottom", fill="x")

    def _create_main(self):
        # one horizontal paned window to hold a tree of suites, tests and keywords
        # on the left, and the rest of the windows on the right.
        hpw = tk.PanedWindow(self, orient="horizontal",
                             borderwidth=0,
                             sashwidth=4, sashpad=0)
        hpw.pack(side="top", fill="both", expand=True)
        vpw = tk.PanedWindow(self, orient="vertical",
                              borderwidth=0,
                              sashwidth=4, sashpad=0)

        self.log_tree = RobotLogTree(hpw, auto_open=("failed","suite","test","keyword"))
        self.varlist = VariableList(vpw)
        self.input = tk.Text(vpw, wrap="word", height=4)
        self.log_messages = RobotLogMessages(vpw)

        hpw.add(self.log_tree, width=500)
        hpw.add(vpw)
        vpw.add(self.varlist, height=150)
        vpw.add(self.log_messages, height=150)
        vpw.add(self.input, height=100)
        self.listeners = (self.log_tree, self.log_messages)

    def reset(self):
        '''Reset all of the windows to their initial state'''
        self.log_tree.reset()
        self.log_messages.reset()
        self.varlist.reset()

    def _listen(self, cmd, *args):
        self.event_id += 1
        self.set_running_state()

        for listener in self.listeners:
            listener.listen(self.event_id, cmd, args)

        if cmd == "pid":
            # our signal that a new test is starting
            self.reset()
            self.set_running_state()

        if cmd == "log_message":
            attrs = args[0]
            if attrs["level"] == "DEBUG":
                if attrs["message"].strip().startswith(":break:"):
                    # this is a signal from the 'breakpoint' keyword
                    self.remote_port = attrs["message"].split(":")[2]
                    self.log.debug("remote port=%s" % self.remote_port)
                    self.set_break_state()
                    self.refresh_vars()

        if cmd in ("start_test", "start_suite", "start_keyword"):
            name = args[0]
            cmd_type = cmd.split("_")[1]
            self.stack.append((cmd_type, name))
            self.update_display()

        elif cmd in ("end_test", "end_suite", "end_keyword"):
            cmd_type = cmd.split("_")[1]
            self.stack.pop()
            self.update_display()

        elif cmd == "close":
            self.set_idle_state()

    def update_display(self):
        '''Refresh all of the status information in the GUI'''
        s = ".".join([x[1] for x in self.stack]).strip()
        self.statusbar.message(s, clear=True, lifespan=0)

class InputWindow(tk.Text):
    _space_splitter = re.compile(' {2,}')
    _pipe_splitter = re.compile(' \|(?= )')

    def __init__(self, *args, **kwargs):
        pass
        tk.Text.__init__(self, *args, **kwargs)

    def get_code(self):
        raw = self.get_raw_code()
        return self._parse(raw)

    def _parse(self, string):
        cells = []
        for line in string.split("\n"):
            row = line.rstrip().replace('\t', '  ')
            if not row.startswith('| '):
                cells.extend(self._space_splitter.split(tmp_row))
            if row.endswith(' |'):
                row = row[1:-1]
            else:
                row = row[1:]

            cells.extend(self._pipe_splitter.split(row))
        print "=>", " | ".join(row)
        return cells

        
    def get_raw_code(self):
        # eventually this can be fancier; for now it's good enough.
        # perhaps later I can a) get the current line, b) see if
        # it's a continuation line; if so, get all predecessors, 
        # and c) check to see if any continuation lines follow
        return self.get("sel.first", "sel.last")

if __name__ == "__main__":
    app = MonitorApp()
    app.mainloop()
