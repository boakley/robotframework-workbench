import Tkinter as tk
import ttk
from rwb.widgets import HighlightMixin
#from editor.api import AbstractEditorPage

class TextWithHighlight(tk.Text, HighlightMixin):
    '''Text widget with the HighlightMixin'''
    pass

class AbstractEditorPage(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        nameframe = ttk.Frame(self, height=32)
        nameframe.pack(side="top", fill="x")

    def grid(self, *args, **kwargs):
        raise Exception("you must use pack for this container")

#class HelpPage(AbstractEditorPage):
class ShortcutPage(AbstractEditorPage):
    def __init__(self, parent):
        AbstractEditorPage.__init__(self, parent)
        self.name = "Help - Shortcuts"
        self.text = TextWithHighlight(self, wrap="word", borderwidth=0, highlightthickness=0)
        self.text.pack(side="top", fill="both", expand="True")
        self.text.insert("insert", BINDINGS.strip())
        self.text.configure(tabs=["2c",])
        self.text.tag_configure("b", foreground="red")
        self.text.tag_configure("dd", lmargin1="2c", lmargin2="2c")
        self.text.tag_configure("dt", foreground="blue")

        self.text.foreach_pattern("</?dl>", lambda: self.text.delete("matchStart", "matchEnd"))
        self.text.foreach_pattern("<dd>.*?</dd>", self._do_dd)
        self.text.foreach_pattern("<dt>.*?</dt>", self._do_dt)
        self.text.foreach_pattern("<b>.*?</b>", self._do_bold)

    def _do_dd(self):
        print "do_dd!"
        self.text.delete("matchEnd-5c", "matchEnd")
        self.text.delete("matchStart", "matchStart+4c")
        self.text.insert("matchStart", "\t")
        self.text.tag_add("dd", "matchStart", "matchEnd")

    def _do_dt(self):
        self.text.delete("matchEnd-5c", "matchEnd")
        self.text.delete("matchStart", "matchStart+4c")
        self.text.tag_add("dt", "matchStart", "matchEnd")

    def _do_bold(self):
        self.text.delete("matchEnd-4c", "matchEnd")
        self.text.delete("matchStart", "matchStart+3c")
        self.text.tag_add("b", "matchStart", "matchEnd")

class HelpPage(AbstractEditorPage):
    def __init__(self, parent):
        AbstractEditorPage.__init__(self, parent)
#        tk.Frame.__init__(self, parent)
        self.name = "Help"
        self.text = TextWithHighlight(self, wrap="word", borderwidth=0, highlightthickness=0)
        self.text.pack(side="top", fill="both", expand="True")
        self.text.insert("insert", HELP.strip())
        self.text.tag_configure("red", foreground="red")

        self.text.foreach_pattern("\*.*?\*", self._do_bold)

    def _do_bold(self):
        self.text.delete("matchEnd-1c")
        self.text.delete("matchStart")
        self.text.tag_add("red", "matchStart", "matchEnd")

HELP = '''
Wouldn't it be *great*...
'''

BINDINGS = '''
<dl>
<dt>Tab</dt><dd>the tab is <b>special!</b> How special? Let me tell you! asd;l ;aslkdjf ;asldfj;asldasldf asdf jasdlfj as;dlfjas ;dfjas;dfj;a sdf;asdfa sdfasdf 
new line
another new line
</dd>
<dt>Control-n</dt>
<dd>blah blah blah control-n</dd>
</dl>
'''
