import Tkinter as tk

class HighlightMixin(object):
    '''A mixin class that adds methods for highlighting text'''
    def highlight_pattern(self, pattern, tag, start="1.0", end="end", whole_lines=False):
        '''Apply the given tag to all text that matches the given pattern'''

        callback=lambda tag=tag, whole_lines=whole_lines: self.tag_add(tag, "matchStart", "matchEnd")
        self.foreach_pattern(pattern, callback, start, end)

    def _apply_tag(tag, whole_lines):
        if whole_lines:
            self.tag_add(tag, "matchStart linestart","matchEnd lineend +1c")
        else:
            self.tag_add(tag, "matchStart","matchEnd")
        
    def foreach_pattern(self, pattern, callback, start="1.0", end="end"):
        '''Call a function for every instance of a pattern
        
        For each match this function will set the marks 'matchStart' and
        'matchEnd' before calling the function.
        '''

        start = self.index(start)
        end = self.index(end)
        self.mark_set("matchStart",start)
        self.mark_set("matchEnd",start)
        self.mark_set("searchLimit", end)

        countvar = tk.IntVar(master=self, name="::__foreach_%s__"% id(self))
        while True:
            index = self._search(pattern, "matchEnd","searchLimit",
                                 count=countvar, regexp=True, nolinestop=True)
            count = countvar.get()

            if index == "" or count == 0: break
            self.mark_set("matchStart", index)
            self.mark_set("matchEnd", "%s+%sc" % (index,count))
            callback()
        
    def _search(self, pattern, index, stopindex=None, forwards=None, 
               backwards=None, exact=None, regexp=None, nocase=None,
               count=None, elide=None, nolinestop=None):
        '''Standard search method, but with support for the nolinestop
        option which is new in tk 8.5 but not supported by tkinter out
        of the box.
        '''
        args = [self._w, 'search']
        if forwards: args.append('-forwards')
        if backwards: args.append('-backwards')
        if exact: args.append('-exact')
        if regexp: args.append('-regexp')
        if nocase: args.append('-nocase')
        if elide: args.append('-elide')
        if nolinestop: args.append("-nolinestop")
        if count: args.append('-count'); args.append(count)
        if pattern and pattern[0] == '-': args.append('--')
        args.append(pattern)
        args.append(index)
        if stopindex: args.append(stopindex)
        return str(self.tk.call(tuple(args)))
