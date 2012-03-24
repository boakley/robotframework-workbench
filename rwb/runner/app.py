import Tkinter as tk
import ttk
import tkFont
from robot_console import RobotConsole
from robot_log import RobotLog
from listener import RemoteRobotListener
from robot_tally import RobotTally
import sys

class RunnerApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.wm_geometry("600x600") # <shrug>
        self.tally = RobotTally()
        self._create_fonts()
        self._create_menubar()
        self._create_toolbar()
        self._create_notebook()

        self._listener = RemoteRobotListener(self, self._listen)
        self._port = self._listener.port
        label = ttk.Label(self, text="port: %s" % self._port)
        label.pack(side="bottom", fill="x")

        self._poll_job_id = None
        self.process = None

    def _create_menubar(self):
        self.menubar = tk.Menu(self)
        self.configure(menu=self.menubar)
        self.fileMenu = tk.Menu(self, tearoff=False)
        self.fileMenu.add_command(label="Exit", command=self._on_exit)
    
    def _create_toolbar(self):
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(side="top", fill="x")
        s = ttk.Style()
        s.configure('BigButton.TButton', font="big_font")
        self.start = ttk.Button(self.toolbar, text="Start", command=self._on_start, 
                                style="BigButton.TButton", takefocus=False)
        self.stop =  ttk.Button(self.toolbar, text="Stop", command=self._on_stop, 
                                style="BigButton.TButton", takefocus=False)
        # this is all so very gross. Surely I can do better! (and don't call my Shirley!)
        label = {
            "critical": ttk.Label(self.toolbar, text="critical", foreground="darkgray"),
            "all": ttk.Label(self.toolbar, text="all", foreground="darkgray"),
            "pass": ttk.Label(self.toolbar, text="pass", foreground="darkgray"),
            "fail": ttk.Label(self.toolbar, text="fail", foreground="darkgray"),
            "total": ttk.Label(self.toolbar, text="total", foreground="darkgray"),
            }
        value = {
            ("critical","pass"): ttk.Label(self.toolbar, text="38", width=5, 
                                       font="big_font", anchor="e", 
                                       textvariable=self.tally["critical","pass"]),
            ("critical","fail"): ttk.Label(self.toolbar, text="0", width=5, 
                                       font="big_font", anchor="e",
                                       textvariable=self.tally["critical","fail"]),
            ("critical","total"): ttk.Label(self.toolbar, text="38", width=5, 
                                        font="big_font", anchor="e",
                                        textvariable=self.tally["critical","total"]),
            ("all","pass"): ttk.Label(self.toolbar, text="38", width=5, 
                                      font="medium_font", anchor="e",
                                      textvariable=self.tally["all","pass"]),
            ("all","fail"): ttk.Label(self.toolbar, text="0", width=5, 
                                      font="medium_font", anchor="e",
                                      textvariable=self.tally["all","fail"]),
            ("all","total"): ttk.Label(self.toolbar, text="38", width=5, 
                                   font="medium_font", anchor="e",
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

        self.start.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=4, pady=4)
        self.stop.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=4, pady=4)

        self.toolbar.grid_columnconfigure(2, weight=2)
        self.value = value

    def add_result(self, result):
        print "result:", result

    def poll(self, delay):
        if self.process:
            (stdout, stderr) = self.process.read()
            self.robot_console.append(stderr, "stderr")
            self.robot_console.append(stdout, "stdout")
        self._poll_job_id = self.after(delay, self.poll, delay)

    def _create_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.robot_console = RobotConsole(self.notebook)
        self.robot_log = RobotLog(self.notebook)
        self.notebook.add(self.robot_log, text="Log")
        self.notebook.add(self.robot_console, text="Console")
        self.notebook.pack(side="top", fill="both", expand=True)

    def _create_fonts(self):
        # Throughout the app, fonts will typically be referenced
        # by their name so we don't have to pass references around.
        # Tk named fonts are a wonderful thing. 
        default_font = self._clone_font("TkDefaultFont", "default_font")
        base_size = default_font.cget("size")

        fixed_font = self._clone_font("TkFixedFont", "fixed_font")
        fixed_bold_font = self._clone_font("fixed_font", "fixed_bold_font", weight="bold")
        fixed_italic_font = self._clone_font("fixed_font", "fixed_italic_font", slant="italic")
        big_font = self._clone_font("default_font", "big_font", size=int(base_size*2.0))
        medium_font = self._clone_font("default_font", "medium_font", size=int(base_size*1.5))
#        bigButtonFont = tkFont.Font(name="bigButtonFont")
#        bigButtonFont.configure(**tkFont.nametofont("TkDefaultFont").configure())
#        bigButtonFont.configure(size=24)

        # save a reference to the fonts so they don't get GC'd
        self.fonts = (default_font, fixed_font, fixed_bold_font, fixed_italic_font, 
                      big_font, medium_font)

    def _clone_font(self, original_font_name, new_font_name, **kwargs):
        new_font = tkFont.Font(name=new_font_name)
        new_font.configure(**tkFont.nametofont(original_font_name).configure())
        new_font.configure(**kwargs)
        return new_font                                      

    def _listen(self, name, *args):
        self.robot_log.add(name, *args)
                       
        # bleh. I hate how I implemented this. 
        if name == "end_test":
            (name, attrs) = args
            self.tally.add_result(attrs)
            if self.tally.get("critical","fail") > 0:
                self.value["critical","fail"].configure(foreground="red")

    def _on_start(self):
        from tsubprocess import Process
        kbot = "t:/tools/kbot.exe"
        listener = "rwb/runner/socket_listener.py:%s" % self._port
        args = ["--listener", listener, "--log", "NONE", "--report", "NONE"]
        files = sys.argv[1:]
#        files = ["sleeper.txt"]
        cmd = [kbot] + args + files
        print "cmd:", cmd
        self.robot_log.add("start_process", cmd)
        self.process = Process(cmd)
        if self._poll_job_id is not None:
            self.after_cancel(self._poll_job_id)
            self._poll_job_id = None
        self.poll(100)

    def _on_stop(self):
        if self.process:
            self.process.terminate()

    def _on_exit(self):
        self.destroy()
        sys.exit(0)


        
if __name__ == "__main__":
    app = RunnerApp()
    app.mainloop()
