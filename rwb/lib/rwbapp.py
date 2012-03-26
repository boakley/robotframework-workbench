import Tkinter as tk
import logging
import sys

class AbstractRwbApp(tk.Tk):
    def __init__(self, name):
        tk.Tk.__init__(self)
        self._initialize_logging(name)
        self.log.debug("logging has been initiated")

    def _initialize_logging(self, name):
        formatter = logging.Formatter("%(levelname)s: %(module)s.%(funcName)s: %(message)s")
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        # this log level needs to come from settings or the
        # command line or something...
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(handler)
        self.log = logging.getLogger(name)
