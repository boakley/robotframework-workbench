import Tkinter as tk

'''
   Seems to work, sorta. This is a work in progress, however, so set
   expectations accordingly. 
'''
class TreeviewTooltip(object):
    def __init__(self, parent, delay=1000, callback=None):
        self.parent = parent
        self._callback = callback
        self._tipwindow = None
        self._id = None
        self._delay = delay
        self.parent.bind("<Enter>", self._on_enter)
        self.parent.bind("<Leave>", self._on_leave)
        self.parent.bind("<Any-ButtonPress>", self._on_leave)
        self.parent.bind("<Motion>", self._on_motion)
        self._tipwindow = tk.Toplevel(self.parent)
        self._tipwindow.wm_overrideredirect(True)
        # it would be nice if we could use some visual tricks 
        # to jazz this up a bit (such as ever-so-slightly rounded
        # corners, a fake drop shadow, very subtle gradient, etc)
        self._tip = tk.Label(self._tipwindow, background="#f5f5dc", borderwidth=1, relief="solid") # ffffe0 = light  yellow
        self._tip.pack(side="top", fill="both", expand=True, ipadx=10, ipady=2)
        if self._tipwindow.tk.call("tk", "windowingsystem") == 'aqua':
            self._tipwindow.tk.call("::tk::unsupported::MacWindowStyle", "style", 
                                    self._tipwindow._w, "help", "none")
        self._hide_tooltip()

    def _show_tooltip(self, x, y):
        (px, py) = self.parent.winfo_pointerxy()
        element = self.parent.identify_row(y)
        self._tipwindow.wm_geometry("+%d+%d" % (px,py-30))
        if self._callback is not None:
            text = self._callback(element)
            if text != "":
                self._tip.configure(text=text)
                self._tipwindow.wm_deiconify()

    def _hide_tooltip(self):
        self._tipwindow.wm_withdraw()

    def _on_enter(self, event=None):
        self._schedule_tooltip(event.x, event.y)

    def _on_motion(self, event=None):
        self._schedule_tooltip(event.x, event.y)

    def _on_leave(self, event=None):
        self._cancel_tooltip()
        if self._tipwindow is not None:
            self._tipwindow.wm_withdraw()

    def _cancel_tooltip(self):
        self._hide_tooltip()
        if self._id is not None:
            self.parent.after_cancel(self._id)
            self._id = None

    def _schedule_tooltip(self, x, y):
        self._cancel_tooltip()
        self._id = self.parent.after(self._delay, self._show_tooltip, x, y)

    
