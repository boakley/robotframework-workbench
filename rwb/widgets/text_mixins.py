import Tkinter as tk
import tcl

class TextCallbackMixin(object):
    '''A mixin class that adds ability to call a function when the widget is modified

    Example:

    class CustomText(tk.Text, TextCallbackMixin):
        def __init__(self, *args, **kwargs):
            tk.Text.__init__(self, *args, **kwargs)
            TextCallbackMixin.__init__(self, *args, **kwargs)
            self.add_post_change_hook("insert", self._on_insert)
            self.add_post_change_hook("delete", self._on_delete)
            self.add_post_change_hool("mark", self._on_mark)

        def _on_insert(self, result, command, *args):
            print "on insert...", args, "=>", result
            import sys; sys.stdout.flush()

        def _on_delete(self, result, command, *args):
            print "on delete...", args, "=>", result
            import sys; sys.stdout.flush()

        def _on_mark(self, result, command, *args):
            print "on mark...", args, "=>", result
            import sys; sys.stdout.flush()

    '''

    def __init__(self, *args, **kwargs):
        post_change_hook = self.register(self._post_change_hook)
        self.hooks = {"insert": [], "delete": [], "replace": [], "mark": []}
        widget = str(self)
        self.tk.eval(tcl.CREATE_WIDGET_PROXY)
        self.tk.eval('''
            rename {widget} _{widget}
            interp alias {{}} ::{widget} {{}} widget_proxy _{widget} {post_change_hook}
        '''.format(widget=widget, post_change_hook=post_change_hook))

    def add_post_change_hook(self, which, cmd):
        '''Register a command to be called whenever the given command occurs

        command must be one of the following: insert, delete, replace, mark

        "mark" refers to the command that sets the insertion cursor (such 
        as when a user clicks in the window, presses the arrow keys, etc). It
        is only called when the underlying command "mark set insert" is called.
        '''
        self.hooks[which].append(cmd)

    def _post_change_hook(self, result, command, *args):
        for func in self.hooks[command]:
            try:
                func(result, command, *args)
            except Exception, e:
                print "warning: exception in post_change_hook:", e

