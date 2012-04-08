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

import tkFont

class FontScheme(object):
    '''A collection of fonts

    The fonts in a font scheme are all based off of two core fonts: a
    variable width font and a fixed width font. By default these are
    the Tkinter "TkDefaultFont" and "TkFixedFont" fonts.
    '''
    def __init__(self, variable_base=None, fixed_base=None):
        if variable_base is None:
            variable_base = tkFont.nametofont("TkDefaultFont")
        if fixed_base is None:
            fixed_base = tkFont.nametofont("TkFixedFont")

        self.default = self.clone_font(variable_base, "default")
        self.fixed = self.clone_font(fixed_base, "fixed")
        self._reset()

    def config_variable(self, **kwargs):
        '''Configure the base variable_width_font'''
        for font in (self.default, self.bold, self.italic):
            font.configure(**kwargs)

    def config_fixed(self, **kwargs):
        '''Configure the base fixed width font'''
        for font in (self.fixed, self.fixed_bold, self.fixed_italic):
            font.configure(**kwargs)
        
    def _reset(self):
        '''Reconfigure all fonts based on the base fonts'''
        self.bold = self.clone_font(self.default, "bold", weight="bold")
        self.italic = self.clone_font(self.default, "italic", slant="italic")
        self.heading = self.clone_font(self.default, "header", weight="bold",
                                       size = int(self.default.actual()["size"])+4)
        self.fixed_bold = self.clone_font(self.fixed, "fixed_bold", weight="bold")
        self.fixed_italic = self.clone_font(self.fixed, "fixed_italic", slant="italic")

    def clone_font(self, base_font, new_name, **kwargs):
        '''Make a copy of a font, then apply unique settings'''
        new_font = tkFont.Font(name="%s_font" % new_name)
        new_font.configure(**base_font.configure())
        new_font.configure(**kwargs)
        return new_font

if __name__ == "__main__":
    import Tkinter as tk
    def on_big():
        fonts.config_variable(size=64)
        fonts.config_fixed(size=64)
    root = tk.Tk()
    button = tk.Button(text="BIG!", command=on_big)
    button.pack()
    fonts = FontScheme()
    fonts.config_variable(family="Helvetica")
    fonts.config_fixed(family="Courier")
    for font in (fonts.default, fonts.bold, fonts.italic,
                 fonts.fixed, fonts.fixed_bold, fonts.fixed_italic):
        text="%s: %s" % (font.name, str(font.actual()))
        tk.Label(root, text=text, anchor="w", font=font).pack(fill="x")
    root.mainloop()

