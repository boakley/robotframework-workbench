''' SearchEntry - entry widget with search icon and rounded ends

'''

import Tkinter as tk
import ttk

class SearchBox(ttk.Entry):
    image1 = None
    image2 = None
    def __init__(self, parent, *args, **kwargs):
        ttk.Entry.__init__(self, parent, *args, **kwargs)
        # what an awful hack. This really should be part of
        # the style. For now, this is good enough. 
        self.parent = parent
        if self.image1 is None:
            self._initialize_style()

        # argh! ttk style layout remain a big mystery to me. Even though
        # the style layout includes the "Search.cancel" element, it's not
        # showing up. Why? I have no idea. So, we'll go old school
        # get this image to show up using the layout, so we'll go
        # and place a label there. *sigh*. 
        self.cancel_label = tk.Label(self, image=self.cancel_image, background="white", 
                                     borderwidth=0, highlightthickness=0,
                                     cursor = "left_ptr")
        self.cancel_label.place(relx=1.0, rely=.5, anchor="e", x=-8)
        self.cancel_label.bind("<1>", self._on_cancel)
        self.bind("<Escape>", self._on_cancel)

    def _on_cancel(self, event):
        self.delete(0, "end")
#        self._stringvar.set("")
        self.cancel()
        return "break"

    def cancel(self):
        # do nothing; subclasses can override, obviously
        pass

    def _initialize_style(self):
        self.normal_image = tk.PhotoImage(data=image_data, format="gif -index 0")
        self.focus_image = tk.PhotoImage(data=image_data, format="gif -index 1")
        self.cancel_image = tk.PhotoImage(data=cancel_image_data)
        ttk.Style().element_create("Search.cancel", 
                                   "image", self.cancel_image, 
                                   sticky="e")
        ttk.Style().element_create("Search.frame", 
                                   "image", self.normal_image, ("focus", self.focus_image),
                                   border=(22, 7, 14), sticky="ew")
        ttk.Style().layout("Search.entry", [
                ("Search.frame", {"sticky": "nsew", "border": 1, "children": [
                            ("Entry.padding", {"sticky": "nsew", "children": [
                                        # this causes space to be reserved, but it's
                                        # not showing up. I have no idea why.
                                        ("Search.cancel", {"side": "right"}),
                                        ("Entry.textarea", {"sticky": "nsw"}),
                                        ]}),
                            ]})
                ])
        self.configure(style="Search.entry", width=40)
        
class SearchEntry(SearchBox):
    def __init__(self, parent, *args, **kwargs):
        
        SearchBox.__init__(self, parent, *args, **kwargs)
        validatecommand = (self.register(self._on_validate), "%P")
        self._stringvar = tk.StringVar()
        self.configure(validate="key", validatecommand=validatecommand,
                       textvariable=self._stringvar)

        self.bind("<Return>", self._on_next)
        self.bind("<Control-n>", self._on_next)
        self.bind("<Control-p>", self._on_previous)
        self.bind("<Control-g>", self._on_next)
        self.bind("<F3>", self._on_next)

    def _on_previous(self, event):
        self.previous()
        return "break"

    def _on_next(self, event):
        self.next()
        return "break"

    def cancel(self):
        '''Remove all highlighting and reset search string'''
        self.reset()
        target = self.parent.get_search_target()
        
    def next(self):
        '''Select the next match and move the cursor to it'''
        target = self.parent.get_search_target()
        search_range = target.tag_nextrange("find", "insert")
        # if the cursor is inside the range we just found, look a 
        # little further
        if (len(search_range) == 2 and
            target.compare("insert", "<=", search_range[1]) and
            target.compare("insert", ">=", search_range[0])):
            search_range = target.tag_nextrange("find", search_range[1])
            
        # if the range is null, wrap around to the start of the widget
        if len(search_range) == 0:
            search_range = target.tag_nextrange("find", 1.0)
            self.bell()

        # if, after all that, the range is still null, well, blimey!
        if len(search_range) == 0:
            self.bell()
        else:
            self._mark_current(*search_range)


    def previous(self):
        '''Select the previous match and move the cursor to it'''
        target = self.parent.get_search_target()
        search_range = target.tag_prevrange("find", "insert")
        # if the cursor is inside the range we just found, look a 
        # little further
        if (len(search_range) == 2 and
            target.compare("insert", "<=", search_range[1]) and
            target.compare("insert", ">=", search_range[0])):
            search_range = target.tag_prevrange("find", search_range[0])
            
        # if the range is null, wrap around to the end of the widget
        if len(search_range) == 0:
            search_range = target.tag_prevrange("find", "end")
            self.bell()

        # if, after all that, the range is still null, well, blimey!
        if len(search_range) == 0:
            self.bell()
        else:
            self._mark_current(*search_range)

    def _on_validate(self, P):
        '''Called whenever the search string changes
        
        This method will cancel any existing search that
        is in progress, then start a new search if the passed
        in string is not empty

        This is called from the entry widget validation command, so 
        even though we're not validating anything per se, we still
        need to return True or this method will stop being called. 
        '''
        self.reset()
        if len(P) > 0:
            self.begin(P)
        return True

    def begin(self, pattern, start="insert"):
        '''Begin a new search'''
        target = self.parent.get_search_target()

        self.reset()
        start = target.index(start)

        range1 = (start, "end")
        if target.compare(start, "!=", "1.0"):
            range2 = ("1.0", start)
        else:
            range2 = ()

        # tkinter's text widget doesn't support the -all option for searching,
        # so we'll have to directly interface with the tcl subsystem
        command = [target._w, "search", "-nocase", "-all", "-forwards"]
        command.append(pattern)

        # search first from start to EOF, then from 1.0 to 
        # the starting point. Why? Most likely the user is
        # wanting to find the next occurrance. This simply
        # optimizes the search so the first match is closest
        # to the insertion cursor
        result1 = self.tk.call(tuple(command + ["insert linestart", "end"]))
        result2 = self.tk.call(tuple(command + ["1.0", "insert lineend"]))

        # why reverse result2? It represents results above the
        # starting point, so if result1 is null, this guarantees
        # that the first result is nearest the search start
        result = list(result1) + list(reversed(result2))
        if len(result) > 0:
            i = result[0]
            self._mark_current(i, "%s + %sc" % (i, len(pattern)))
        for index in result:
            target.tag_add("find", index, "%s + %sc" % (index, len(pattern)))

    def _mark_current(self, start, end):
        '''Mark the 'current' match'''
        target = self.parent.get_search_target()
        target.tag_remove("current_find", 1.0, "end")
        target.tag_add("current_find", start, end)
        target.tag_remove("sel", 1.0, "end")
        target.tag_add("sel", start, end)
        target.mark_set("insert", start)
        target.tag_raise("sel")
        target.tag_raise("current_find")
        target.see(start)

    def reset(self):
        '''Reset the searching mechanism'''
        target = self.parent.get_search_target()
        target.tag_configure("find", background="yellow", foreground="black")
        target.tag_configure("current_find", 
                             background=target.tag_cget("sel", "background"),
                             foreground=target.tag_cget("sel", "foreground"))
        target.tag_remove("current_find", 1.0, "end")
        target.tag_remove("find", 1.0, "end")
        target.tag_raise("find")
        target.tag_raise("current_find", "find")
        target.tag_raise("current_find", "sel")


cancel_image_data = '''
    R0lGODlhEAAQAMQZAMPDw+zs7L+/v8HBwcDAwLW1teLi4t7e3uDg4MLCwuHh4e7u7t/f38TExLa2
    tre3t7i4uL6+vu/v77q6uu3t7b29vby8vLm5ubu7u+3t7QAAAAAAAAAAAAAAAAAAAAAAACH5BAEA
    ABkALAAAAAAQABAAAAWNYCaOZFlWV6pWZlZhTQwAyYSdcGRZGGYNE8vo1RgYCD2BIkK43DKXRsQg
    oUQiFAkCI3iILgCLIEvJBiyQiOML6GElVcsFUllD25N3FQN51L81b2ULARN+dhcDFggSAT0BEgcQ
    FgUicgQVDHwQEwc+DxMjcgITfQ8Pk6AlfBEVrjuqJhMOtA4FBRctuiUhADs=
'''

image_data = '''
    R0lGODlhKgAaAOfnAFdZVllbWFpcWVtdWlxeW11fXF9hXmBiX2ZnZWhpZ2lraGxua25wbXJ0
    cXR2c3V3dHZ4dXh6d3x+e31/fH6AfYSGg4eJhoiKh4qMiYuNio2PjHmUqnqVq3yXrZGTkJKU
    kX+asJSWk32cuJWXlIGcs5aYlX6euZeZloOetZial4SftpqbmIWgt4GhvYahuIKivpudmYei
    uYOjv5yem4ijuoSkwIWlwYmlu56gnYamwp+hnoenw4unvaCin4ioxJCnuZykrImpxZmlsoaq
    zI2pv6KkoZGouoqqxpqms4erzaOloo6qwYurx5Kqu5untIiszqSmo5CrwoysyJeqtpOrvJyo
    tZGsw42typSsvaaopZKtxJWtvp6qt4+uy6epppOuxZCvzKiqp5quuZSvxoyx06mrqJWwx42y
    1JKxzpmwwaqsqZaxyI6z1ZqxwqutqpOzz4+01qyuq56yvpizypS00Jm0y5W10Zq1zJa20rCy
    rpu3zqizwbGzr6C3yZy4z7K0saG4yp250LO1sqK5y5660Z+70qO7zKy4xaC806S8zba4taG9
    1KW9zq66x6+7yLi6t6S/1rC8yrm7uLO8xLG9y7q8ubS9xabB2anB07K+zLW+xrO/za7CzrTA
    zrjAyLXBz77BvbbC0K/G2LjD0bnE0rLK28TGw8bIxcLL07vP28HN28rMycvOyr/T38DU4cnR
    2s/RztHT0NLU0cTY5MrW5MvX5dHX2c3Z59bY1dPb5Nbb3dLe7Nvd2t3f3NXh797g3d3j5dnl
    9OPl4eTm4+Ln6tzo9uXn5Obo5eDp8efp5uHq8uXq7ejq5+nr6OPs9Ovu6unu8O3v6+vw8+7w
    7ezx9O/x7vDy7/Hz8O/19/P18vT38/L3+fb49Pf59vX6/fj69/b7/vn7+Pr8+ff9//v9+vz/
    +/7//P//////////////////////////////////////////////////////////////////
    /////////////////////////////////yH/C05FVFNDQVBFMi4wAwEAAAAh+QQJZAD/ACwC
    AAIAKAAWAAAI/gD/CRz4bwUGCg8eQFjIsGHDBw4iTLAQgqBFgisuePCiyJOpUyBDihRpypMi
    Lx8qaLhIMIyGFZ5sAUsmjZrNmzhzWpO2DJgtTysqfGDpxoMbW8ekeQsXzty4p1CjRjUXrps3
    asJsuclQ4uKKSbamMR3n1JzZs2jRkh1HzuxVXX8y4CDYAwqua+DInVrRwMGJU2kDp31KThy1
    XGWGDlxhi1rTPAUICBBAoEAesoIzn6Vm68MKgVAUHftmzhOCBCtQwQKSoABgzZnJdSMmyIPA
    FbCotdUQAIhNa9B6DPCAGbZac+SowVIMRVe4pwkA4GpqDlwuAAmMZx4nTtfnf1mO5JEDNy46
    MHJkxQEDgKC49rPjwC0bqGaZuOoZAKjBPE4NgAzUvYcWOc0QZF91imAnCDHJ5JFAAJN0I2Ba
    4iRDUC/gOEVNDwIUcEABCAgAAATUTIgWOMBYRFp80ghiAQIIVAAEAwJIYI2JZnUji0XSYAYO
    NcsQA8wy0hCTwAASXGOiONFcxAtpTokTHznfiLMNMAkcAMuE43jDC0vLeGOWe2R5o4sn1LgH
    GzkWsvTPMgEOaA433Ag4TjjMuDkQMNi0tZ12sqWoJ0HATMPNffAZZ6U0wLAyqJ62RGoLLrhI
    aqmlpzwaEAAh+QQJZAD/ACwAAAAAKgAaAAAI/gD/CRw40JEhQoEC+fGjcOHCMRAjRkxDsKLF
    f5YcAcID582ZjyBDJhmZZIjJIUySEDHiBMhFghrtdNnRAgSHmzhz6sTZQcSLITx+CHn5bxSk
    Nz5MCMGy55CjTVCjbuJEtSrVQ3uwqDBRQwrFi476SHHxow8qXcemVbPGtm21t3CnTaP27Jgu
    VHtuiIjBsuImQkRiiEEFTNo2cOTMKV7MuLE5cN68QUOGSgwKG1EqJqJDY8+rZt8UjxtNunTj
    cY3DgZOWS46KIFgGjiI0ZIsqaqNNjWjgYMUpx8Adc3v2aosNMAI1DbqyI9WycOb4IAggQEAB
    A3lQBxet/TG4cMpI/tHwYeSfIzxM0uTKNs7UgAQrYL1akaDA7+3bueVqY4NJlUhIcQLNYx8E
    AIQ01mwjTQ8DeNAdfouNA8440GBCQxJY3MEGD6p4Y844CQCAizcSgpMLAAlAuJ03qOyQRBR3
    nEHEK+BMGKIui4kDDAAIPKiiYuSYSMQQRCDCxhiziPMYBgDkEaEaAGQA3Y+MjUPOLFoMoUUh
    cKxRC4ngeILiH8Qkk0cCAUzSDZWpzbLEE1EwggcYqWCj2DNADFDAAQUgIAAAEFDDJmPYqNJF
    F1s4cscTmCDjDTjdSPOHBQggUAEQDAgggTWDPoYMJkFoUdRmddyyjWLeULMMMcAsIw0x4wkM
    IME1g25zyxpHxFYUHmyIggw4H4ojITnfiLMNMAkcAAub4BQjihRdDGTJHmvc4Qo1wD6Imje6
    eILbj+BQ4wqu5Q3ECSJ0FOKKMtv4mBg33Pw4zjbKuBIIE1xYpIkhdQQiyi7OtAucj6dt48wu
    otQhBRa6VvSJIRwhIkotvgRTzMUYZ6xxMcj4QkspeKDxxRhEmUfIHWjAgQcijEDissuXvCyz
    zH7Q8YQURxDhUsn/bCInR3AELfTQZBRt9BBJkCGFFVhMwTNBlnBCSCGEIJQQIAklZMXWRBAR
    RRRWENHwRQEBADs=
'''

if __name__ == "__main__":
    root = tk.Tk()

    e1 = SearchEntry(root)
    e1.pack(side="top")
    root.mainloop()
