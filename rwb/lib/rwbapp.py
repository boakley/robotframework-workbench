import Tkinter as tk
import logging
import sys
import ttk

class AbstractRwbApp(tk.Tk):
    def __init__(self, name):
        tk.Tk.__init__(self)
        # toplevel widgets aren't "themed". This frame acts
        # as a themed background for the app as a whole.
        background=ttk.Frame(self)
        background.place(x=0, y=0, relwidth=1, relheight=1)
        self._initialize_logging(name)
        self.log.debug("logging has been initiated")

    def _initialize_logging(self, name):
        formatter = logging.Formatter("%(levelname)s: %(module)s.%(funcName)s: %(message)s")
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(handler)
        self.log = logging.getLogger(name)
