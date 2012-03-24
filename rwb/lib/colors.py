'''Colors - define application-wide color scheme'''

# these colors came from here:
# http://www.colorcombos.com/color-schemes/218/ColorCombo218.html
# background1 = "#dddddd"
# background2 = "#3f547f"
# background3 = "#ffffff"
# accent = "#f58735"
# foreground1 = "#000000"
# foreground2 = background1
# foreground3 = background3

class ColorScheme(object):
    '''Define a standard color palette'''
    def __init__(self, *args, **kwargs):
        # these come from here:
        # http://www.colorcombos.com/color-schemes/6/ColorCombo6.html
        self.accent="red"
        self.background1 = "#666633"
        self.background2 = "#CCCC99"
        self.foreground1 = "#FFFFFF"
        self.foreground2 = "#000000"

