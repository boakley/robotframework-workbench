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
import platform
import os
from rwb.lib import AbstractSettingsFrame
from rwb.lib.configobj import ConfigObj
from rwb.lib.colors import ColorScheme
from rwb.lib.fonts import FontScheme
from rwb.widgets import SettingsDialog

class AbstractRwbApp(tk.Tk):
    def __init__(self, name, default_settings):
        tk.Tk.__init__(self)
        # toplevel widgets aren't "themed". This frame acts
        # as a themed background for the app as a whole.
        background=ttk.Frame(self)
        background.place(x=0, y=0, relwidth=1, relheight=1)

        self.name = name
        self.settings_dialog = None
        self._save_settings_job = None
        self._initialize_logging(name)
        self._initialize_settings(name, default_settings)
        self._initialize_themes()

        self.log.debug("logging has been initiated")

        s = ttk.Style()
        s.configure("Toolbutton", anchor="c")

        self._settings_frames = []

    def register(self, class_):
        if AbstractSettingsFrame in class_.__bases__:
            self._settings_frames.append(class_)
        else:
            raise Exception("register: unexpected object:" + str(class_))

    def _initialize_themes(self):
        self.colors = ColorScheme()
        self.fonts = FontScheme()

    def _initialize_logging(self, name):
        formatter = logging.Formatter("%(levelname)s: %(module)s.%(funcName)s: %(message)s")
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(handler)
        self.log = logging.getLogger(name)

    def show_settings_dialog(self):
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.show()

    def get_settings_frames(self):
        return self._settings_frames

    def get_setting(self, key, default=None):
        '''Return a setting for the given key

        A key is expressed in dot notation (eg: editor.foo.bar)
        The first part of the key should be the app name
        ( eg: editor, runner, kwbrowser)
        '''
        section = self.settings
        keys = key.split(".")
        for key in key.split(".")[:-1]:
            section = section.setdefault(key, {})
        result = section.setdefault(keys[-1], default)
        return result

    def set_setting(self, key, value):
        section = self.settings
        keys = key.split(".")
        for key in key.split(".")[:-1]:
            section = section.setdefault(key, {})
        result = section[keys[-1]] = value
        return result

    def save_settings(self, now=False):
        '''Saves all settings; may delay unless now=True
        
        Because of the delay, it's safe to call this on every keypress
        in a preferences panel if you so wish. Each time this is called
        the timer is reset, which means there shouldn't be a performance
        hit while the user is actively typing -- it will save whenever
        the user takes a break.
        '''
        delay = 3000
        if now:
            self.log.debug("writing settings to disk")
            self.settings.filename = self.settings_path
            self.settings.write()
            if self._save_settings_job is not None:
                self.after_cancel(self._save_settings_job)
                self._save_settings_job = None
        else:
            if self._save_settings_job is not None:
                self.after_cancel(self._save_settings_job)
            self._save_settings_job = self.after(3000, self.save_settings, True)

    def _initialize_settings(self, name, default_settings = {}):
        '''Creates self.settings, a ConfigObj with the apps settings

        See self.get_setting() to see how to retrieve a value
        '''
        
        if platform.system() == "Windows":
            settings_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
            settings_file = "rwb.cfg"
        else:
            settings_dir = os.environ.get("HOME", os.path.expanduser("~"))
            settings_file = ".rwb.cfg"
        self.settings_path = os.path.join(settings_dir, settings_file)
        self.log.debug("settings path: %s" % self.settings_path)
        
        self.settings = ConfigObj(default_settings)

        if os.path.exists(self.settings_path):
            self.log.debug("reading config file '%s'" % self.settings_path)
            try:
                user_settings = ConfigObj(self.settings_path)
                self.settings[name].merge(user_settings[name])
            except Exception, e:
                # need to report this somewhere useful, and 
                # make sure it has some useful information
                self.log.warning("error opening config file: %s" % str(e))
        else:
            self.log.debug("no settings file found.")

