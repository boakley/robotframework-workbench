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
import logging
import sys
import ttk
from rwb.lib import AbstractSettingsFrame

class AbstractRwbApp(tk.Tk):
    def __init__(self, name):
        tk.Tk.__init__(self)
        # toplevel widgets aren't "themed". This frame acts
        # as a themed background for the app as a whole.
        background=ttk.Frame(self)
        background.place(x=0, y=0, relwidth=1, relheight=1)

        self._initialize_logging(name)
        self.log.debug("logging has been initiated")

        s = ttk.Style()
        s.configure("Toolbutton", anchor="c")

        self._settings_frames = []

    def _initialize_logging(self, name):
        formatter = logging.Formatter("%(levelname)s: %(module)s.%(funcName)s: %(message)s")
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(handler)
        self.log = logging.getLogger(name)

    def register(self, class_):
        if AbstractSettingsFrame in class_.__bases__:
            self._settings_frames.append(class_)
        else:
            raise Exception("register: unexpected object:" + str(class_))

    def get_settings_frames(self):
        return self._settings_frames

