'''
Robot Framework Workbench Test Runner

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

TODO: 
  * add progress bar
  * fully implement notion of IDs
  * print currently executing test suite in status bar

'''

import Tkinter as tk
import ttk
import tkFont
import sys
import os
from controller import RobotController
from console import RobotConsole
from log import RobotLogTree, RobotLogMessages
from listener import RemoteRobotListener
from robot_tally import RobotTally
from rwb.lib import AbstractRwbGui
from settings import GeneralSettingsFrame
from tsubprocess import Process
from rwb.widgets import ToolButton
import shlex
import rwb

NAME="runner"
HELP_URL="https://github.com/boakley/robotframework-workbench/wiki/rwb.runner-User-Guide"
DEFAULT_SETTINGS = {
    NAME: {
        "pybot": "python -m robot.runner '%S'",
        }
    }

class RunnerApp(AbstractRwbGui):
    def __init__(self):
        # Among other things, this constructor initializes
        # logging and preferences. 
        AbstractRwbGui.__init__(self, NAME, DEFAULT_SETTINGS)
        self.wm_geometry("800x600")
        self.tally = RobotTally()
        self._create_fonts()
        self._create_menubar()
        self._create_statusbar()
        self._create_toolbar()
#        self._create_command_line()
        self._create_notebook()

        self.register(GeneralSettingsFrame)
        
        self._controller = RobotController(self)
        self._controller.configure(listeners=(self.console,self.log_tree,
                                              self.log_messages, self.tally,
                                              self))

    def status_message(self, message):
        '''Print a message in the statusbar'''
        self.status_label.configure(text=message)

    def _create_statusbar(self):
        self.statusbar = ttk.Frame(self)
        grip = ttk.Sizegrip(self.statusbar)
        grip.pack(side="right")
        self.status_label = tk.Label(self.statusbar, text="", anchor="w")
        self.status_label.pack(side="left", fill="both", expand="true", padx=8)
        self.statusbar.pack(side="bottom", fill="x")

    def _create_menubar(self):
        self.menubar = tk.Menu(self)
        self.configure(menu=self.menubar)

#        self.rwbMenu = tk.Menu(self, tearoff=False)
#        self.menubar.add_cascade(menu=self.rwbMenu, label="rwb", underline=0)
#        self.rwbMenu.add_command(label="Settings", command=self.show_settings_dialog)

        self.file_menu = tk.Menu(self.menubar, tearoff=False)
        self.file_menu.add_command(label="Exit", command=self._on_exit)

        self.help_menu = tk.Menu(self, tearoff=False)
        self.help_menu.add_command(label="View help on the web", command=self._on_view_help)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="About the robotframework workbench", command=self._on_about)

        self.menubar.add_cascade(menu=self.file_menu, label="File", underline=0)
        self.menubar.add_cascade(menu=self.help_menu, label="Help", underline=0)
    
    def _toggle_command(self, collapse=None):
        if self.command_text.winfo_viewable() or collapse==True:
            self.command_text.grid_remove()
            self.command_expander.configure(text=">")
        else:
            self.command_text.grid()
            self.command_expander.configure(text="V")

    def _create_command_line(self):
        self.command_frame = tk.Frame(self, borderwidth=2, relief="groove")
        self.command_expander = ToolButton(self.command_frame, 
                                           imagedata=None, text=">", width=1,
                                           command=self._toggle_command)
        self.command_label = ttk.Label(self.command_frame, text="Command Line", anchor="w")
        self.command_text = tk.Text(self.command_frame, wrap="word", height=3)
        self.command_expander.grid(row=0, column=0)
        self.command_label.grid(row=0, column=1, sticky="w")
        self.command_text.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.command_frame.pack(side="top", fill="x")
        self.command_frame.grid_columnconfigure(1, weight=1)
        self._toggle_command(collapse=True)
        
    def _create_toolbar(self):
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(side="top", fill="x", padx=8)
        s = ttk.Style()
        s.configure('BigButton.TButton', font=self.fonts.big_font)
        self.start_button = ttk.Button(self.toolbar, text="Start", 
                                       command=self.start_test, 
                                       style="BigButton.TButton", 
                                       takefocus=False)
        self.stop_button =  ttk.Button(self.toolbar, text="Stop", 
                                       command=self.stop_test, 
                                       style="BigButton.TButton", 
                                       takefocus=False)
        # this is all so very gross. Surely I can do better! (and don't call my Shirley!)
        label = {
            "critical": ttk.Label(self.toolbar, text="critical", foreground="darkgray"),
            "all":      ttk.Label(self.toolbar, text="all", foreground="darkgray"),
            "pass":     ttk.Label(self.toolbar, text="pass", foreground="darkgray"),
            "fail":     ttk.Label(self.toolbar, text="fail", foreground="darkgray"),
            "total":    ttk.Label(self.toolbar, text="total", foreground="darkgray"),
            }
        value = {
            ("critical","pass"): ttk.Label(self.toolbar, text="38", width=5, 
                                       font=self.fonts.big_font, anchor="e", 
                                       textvariable=self.tally["critical","pass"]),
            ("critical","fail"): ttk.Label(self.toolbar, text="0", width=5, 
                                       font=self.fonts.big_font, anchor="e",
                                       textvariable=self.tally["critical","fail"]),
            ("critical","total"): ttk.Label(self.toolbar, text="38", width=5, 
                                        font=self.fonts.big_font, anchor="e",
                                        textvariable=self.tally["critical","total"]),
            ("all","pass"): ttk.Label(self.toolbar, text="38", width=5, 
                                      font=self.fonts.medium_font, anchor="e",
                                      textvariable=self.tally["all","pass"]),
            ("all","fail"): ttk.Label(self.toolbar, text="0", width=5, 
                                      font=self.fonts.medium_font, anchor="e",
                                      textvariable=self.tally["all","fail"]),
            ("all","total"): ttk.Label(self.toolbar, text="38", width=5, 
                                   font=self.fonts.medium_font, anchor="e",
                                  textvariable=self.tally["all","total"]),
            }

        label["critical"].grid(row=0, column=3, sticky="nse")
        value["critical","pass"].grid(row=0, column=4, sticky="nse")
        value["critical","fail"].grid(row=0, column=5, sticky="nse")
        value["critical","total"].grid(row=0, column=6, sticky="nse")

        label["all"].grid(row=1, column=3, sticky="nse")
        value["all","pass"].grid(row=1, column=4, sticky="nse")
        value["all","fail"].grid(row=1, column=5, sticky="nse")
        value["all","total"].grid(row=1, column=6, sticky="nse")

        label["pass"].grid(row=2, column=4, sticky="nse")
        label["fail"].grid(row=2, column=5, sticky="nse")
        label["total"].grid(row=2, column=6, sticky="nse")

        self.start_button.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=4, pady=4)
        self.stop_button.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=4, pady=4)

        self.stop_button.configure(state="disabled")
        self.toolbar.grid_columnconfigure(2, weight=2)
        self.value = value
        self.tally["critical","fail"].trace_variable("w", self._on_tally_trace)

    def _on_tally_trace(self, name1, name2, mode):
        if self.tally["critical","fail"].get() > 0:
            self.value["critical","fail"].configure(foreground="red")
            self.value["all","fail"].configure(foreground="red")

    def _create_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.console = RobotConsole(self.notebook)
        self.log_tree = RobotLogTree(self.notebook)
        self.log_messages = RobotLogMessages(self.notebook)
        self.notebook.add(self.log_tree, text="Details")
        self.notebook.add(self.console, text="Console")
        self.notebook.add(self.log_messages, text="Messages")
        self.notebook.pack(side="top", fill="both", expand=True)

    def _create_fonts(self):
        '''Create fonts specifically for this app

        This app has some unique features such as the big start/stop
        buttons, so it can't use the font scheme. What it _should_
        do is at least base the fonts off of the scheme, but for 
        now we shall march to the beat of our own drummer.
        '''
        # Throughout the app, fonts will typically be referenced
        # by their name so we don't have to pass references around.
        # Tk named fonts are a wonderful thing. 
        base_size = self.fonts.default.cget("size")
        self.fonts.big_font = self.fonts.clone_font(self.fonts.default, "big_font", 
                                                    size=int(base_size*2.0))
        self.fonts.medium_font = self.fonts.clone_font(self.fonts.default, "medium_font", 
                                                       size=int(base_size*1.5))

    def reset(self):
        self.status_message("")

    def listen(self, event_id, event_name, args):
        '''Update the statusbar based on the passed-in event'''
        if event_name in ("start_suite", "start_test"):
            (name, attrs) = args
            self.status_message(attrs["longname"])
        elif event_name == "close":
            self.status_message(str(self.tally))

    def start_test(self):
        self._controller.configure(args=sys.argv[1:])
        self.stop_button.configure(state="normal")
        self.start_button.configure(state="disabled")
        self._controller.start()

    def stop_test(self):
        controller.stop()
        self.stop_button.configure(state="disabled")
        self.start_button.configure(state="normal")

    def _on_exit(self):
        self.destroy()
        sys.exit(0)

    def _on_view_help(self):
        import webbrowser
        webbrowser.open(HELP_URL)


        
if __name__ == "__main__":
    app = RunnerApp()
    app.mainloop()
