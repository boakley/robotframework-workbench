import Tkinter as tk
import ttk

class ToolButton(ttk.Button):
    def __init__(self, parent, imagedata, tooltip="the tooltip", text=None,command=None):
        self._normal_image = tk.PhotoImage(data=imagedata)

        self.tooltip = tooltip
        # TODO: add support for a disabled image, as well as centered stuff
        # there's an old tclscripting article about how to do that...
        ttk.Button.__init__(self,parent, style="Toolbutton", image=self._normal_image, 
                            command=command, takefocus=False)
        if text is not None:
            # FIXME: this is the wrong place to set the width...
            self.configure(text=text, compound="top", width=5)
        self.bind("<Enter>", self._on_show_tip)
        self.bind("<Leave>", self._on_hide_tip)
        self.tip = tk.Toplevel(self, borderwidth=1, relief="solid")
        self.tip.wm_overrideredirect(True)
        tiplabel = tk.Label(self.tip, text=tooltip, background="lightyellow")
        tiplabel.pack(side="top", fill="both", expand=True)
        self._job = None
        self.tip.wm_withdraw()

        if self.tip.tk.call("tk", "windowingsystem") == 'aqua':
            self.tip.tk.call("::tk::unsupported::MacWindowStyle", "style", self.tip._w, "help", "none")

    def _on_show_tip(self, event):
        self._cancel()
        self._job = self.after(750, self._show_tip)

    def _on_hide_tip(self, event):
        self._cancel()
        self.tip.wm_withdraw()

    def _show_tip(self):
        x0 = self.winfo_rootx()
        y0 = self.winfo_rooty()
        x = x0
        y = y0 + self.tip.winfo_reqheight() + 12
        geometry = "+%d+%d" % (x, y)
        self.tip.wm_geometry(geometry)
        self.tip.deiconify()

    def _cancel(self):
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None
        
        
