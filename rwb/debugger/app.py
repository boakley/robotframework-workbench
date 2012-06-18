''' 
Don't assume this works. It is a hack; I started with copying rwb.monitor 
then just started hacking away.
'''

import ttk
import Tkinter as tk
from rwb.runner.log import RobotLogTree, RobotLogMessages
from rwb.lib import AbstractRwbApp
from rwb.widgets import Statusbar
import xmlrpclib

from rwb.runner.listener import RemoteRobotListener

NAME = "debugger"
DEFAULT_SETTINGS = {
    NAME: {
        "port": 8910,
        "host": "localhost",
        }
    }

class DebuggerApp(AbstractRwbApp):
    def __init__(self):
        AbstractRwbApp.__init__(self, NAME, DEFAULT_SETTINGS)
        self.wm_geometry("900x500")
        port = self.get_setting("debugger.port")
        self.listener = RemoteRobotListener(self, port=port, callback=self._listen)
        self.wm_title("rwb." + NAME)
        self._create_menubar()
        self._create_toolbar()
        self._create_statusbar()
        self._create_main()
        self.stack = []
        self.event_id = 0
        self.wm_protocol("WM_DELETE_WINDOW", self._on_exit)

    def _on_exit(self, *args):
        try:
            # in case the remote robot instance is waiting for us,
            # let's send a continue command
            proxy = xmlrpclib.ServerProxy("http://localhost:8911",allow_none=True)
            proxy.continue_()
        except Exception, e:
            # I probably should log something...
            pass
        self.destroy()
        
    def _create_toolbar(self):
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(side="top", fill="x")
        self.continue_button = ttk.Button(self.toolbar,text="continue", command=self._on_continue)
        self.continue_button.pack(side="left")
        self.continue_button.configure(state="disabled")

    def refresh_vars(self):
        proxy = xmlrpclib.ServerProxy("http://localhost:8911",allow_none=True)
        variables = proxy.get_variables()
        for (key, value) in variables.iteritems():
            # for reasons I don't yet understand, backslashes are getting interpreted
            # as escape sequences. WTF?
            try:
                value = value.replace("\\", "\\\\")
            except: 
                pass
            self.varlist.insert("", "end", text=key, values=(value,))

    def _on_continue(self):
        proxy = xmlrpclib.ServerProxy("http://localhost:8911",allow_none=True)
        proxy.continue_()
        
    def _create_menubar(self):
        self.menubar = tk.Menu(self)
        self.configure(menu=self.menubar)
        self.file_menu = tk.Menu(self.menubar, tearoff=False)
        self.file_menu.add_command(label="Exit", command=self._on_exit)
        self.menubar.add_cascade(menu=self.file_menu, label="File", underline=0)


    def _create_statusbar(self):
        self.statusbar = Statusbar(self)
        self.statusbar.pack(side="bottom", fill="x")
        self.statusbar.add_section("port",12, "port %s" % self.listener.port)
        self.statusbar.add_progress(mode="indeterminate")
        # grip = ttk.Sizegrip(self.statusbar)
        # grip.pack(side="right")
        # self.status_label = ttk.Label(self.statusbar, text="", anchor="w")
        # self.status_label.pack(side="left", fill="both", expand="true", padx=8)
        # self.statusbar.pack(side="bottom", fill="x")

    def _create_main(self):
        pw = ttk.PanedWindow(self, orient="vertical")
        pw.pack(side="right", fill="both", expand=True)

        self.varlist = ttk.Treeview(pw, columns=("value",))
        self.input = tk.Text(pw, wrap="word", height=4)
        self.log_tree = RobotLogTree(self, auto_open=("failed","suite","test","keyword"))
        self.log_messages = RobotLogMessages(pw)
        pw.add(self.varlist, weight=1)
        pw.add(self.log_messages, weight=1)
        pw.add(self.input, weight=0)
        self.log_tree.pack(side="left", fill="y")
        self.listeners = (self.log_tree, self.log_messages)

    def reset(self):
        print "reset..."

    def _listen(self, cmd, *args):
        self.event_id += 1
        for listener in self.listeners:
            listener.listen(self.event_id, cmd, args)

        if cmd == "pid":
            # our signal that a new test is starting
            self.reset()

        if True and cmd == "log_message":
            attrs = args[0]
            if attrs["level"] == "DEBUG":
                if attrs["message"] == ":break:":
                    # this is a signal from the 'breakpoint' keyword
                    self.continue_button.configure(state="normal")
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

    def update_display(self):
        if len(self.stack) == 1:
            self.statusbar.progress_start()
        elif len(self.stack) == 0:
            self.statusbar.progress_stop()

        s = ".".join([x[1] for x in self.stack]).strip()
        self.statusbar.message(s, clear=True, lifespan=0)

if __name__ == "__main__":
    app = MonitorApp()
    app.mainloop()
