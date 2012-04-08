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

# This is just a shell of what it could be. Right now I'm not really
# everaging these in very many places. For the most part it's just
# a good place to define the accent, error and warning  colors.

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
        self.warn = "#663300"
        self.error = "#b22222"
        self.test_pass = "#009900"
        self.test_fail = "#b22222"
