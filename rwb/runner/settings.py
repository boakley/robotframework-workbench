import Tkinter as tk
import ttk
from rwb.lib import AbstractSettingsFrame
import rwb

LABEL1='''Enter a string to use to run your tests. You may include any robot options that you want. The current test suite will be appended to this command.  The default is 'python -m robot.runner'. '''

class GeneralSettingsFrame(AbstractSettingsFrame):
    section = []
    title="General"
    def __init__(self, parent):
        AbstractSettingsFrame.__init__(self, parent)
        self.label = tk.Label(self, text=LABEL1, anchor="w", justify="left")
        self.label.pack(fill="x")
        self.bind("<Configure>", self._on_label_resize)
        self.cmd_text = tk.Text(self, wrap="word", height=4)
        self.cmd_text.pack(side="top", fill="x")
        self.cmd_text.insert("end", rwb.app.get_setting("runner.pybot"), "python -m robot.runner")
        self.cmd_text.bind("<Any-KeyRelease>", self._on_key)

    def _on_key(self, event):
        text = self.cmd_text.get("1.0", "end-1c")
        rwb.app.set_setting("runner.pybot", text)
        rwb.app.save_settings()

    def _on_label_resize(self, event):
        self.update_idletasks()
        width = self.label.winfo_width()
        print "width:", width
        self.label.configure(wraplength=width-20)

    def _save(self):
        pass
