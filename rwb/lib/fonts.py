'''Fonts - define application-wide fonts'''

import tkFont

class FontScheme(object):
    def __init__(self, variable_base="TkDefaultFont", fixed_base="TkFixedFont"):
        self.default = self.clone_font(variable_base, "default")
        self.bold = self.clone_font(variable_base, "bold", weight="bold")
        self.italic = self.clone_font(variable_base, "italic", slant="italic")
        self.heading = self.clone_font(variable_base, "header", weight="bold",
                                       size = int(self.default.actual()["size"])+4)
        self.fixed = self.clone_font(fixed_base, "fixed")
        self.fixed_bold = self.clone_font(fixed_base, "fixed_bold", weight="bold")
        self.fixed_italic = self.clone_font(fixed_base, "fixed_italic", slant="italic")

    def config_variable(self, **kwargs):
        for font in (self.default, self.bold, self.italic):
            font.configure(**kwargs)

    def config_fixed(self, **kwargs):
        for font in (self.fixed, self.fixed_bold, self.fixed_italic):
            font.configure(**kwargs)
        
    def clone_font(self, original_font_name, new_name, **kwargs):
        new_font = tkFont.Font(name="%s_font" % new_name)
        new_font.configure(**tkFont.nametofont(original_font_name).configure())
        new_font.configure(**kwargs)
        return new_font

if __name__ == "__main__":
    import Tkinter as tk
    root = tk.Tk()
    fonts = FontScheme()
    fonts.config_variable(family="Helvetica")
    fonts.config_fixed(family="Courier")
    for font in (fonts.default, fonts.bold, fonts.italic,
                 fonts.fixed, fonts.fixed_bold, fonts.fixed_italic):
        text="%s: %s" % (font.name, str(font.actual()))
        tk.Label(root, text=text, anchor="w", font=font).pack(fill="x")
    root.mainloop()

