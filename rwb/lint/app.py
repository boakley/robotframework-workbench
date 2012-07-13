import logging
import sys
from rwb.lib import AbstractRwbApp
from robot.errors import DataError
from robot.parsing import TestData, ResourceFile

from lint import LintController

NAME = "lint"
DEFAULT_SETTINGS = {
    NAME: {
        # placeholder for future settings
        }
    }

class RobotLintApp(AbstractRwbApp):
    def __init__(self):
        super(RobotLintApp,self).__init__(NAME, DEFAULT_SETTINGS)
        self.checker = LintController()

    def mainloop(self):
        for path in sys.argv[1:]:
            try:
                suite = TestData(parent=None, source=sys.argv[1])
            except DataError:
                # Hmmm. This means it's not a test suite. Maybe it's a 
                # resource file?
                suite = ResourceFile(path)
        
def xTestData(parent=None, source=None, include_suites=[], warn_on_skipped=False):
    '''Open either a test case directory or file, or a resource file

    This was copied from robot.parsing.model.TestData, then modified to support
    opening resource files
    '''
    if os.path.isdir(source):
        return TestDataDirectory(parent, source).populate(include_suites, warn_on_skipped)
    else:
        try:
            return TestCaseFile(parent, source).populate()
        except DataError:
            # the assumption is, if we get a DataError then this is a
            # resource file. That's probably not a very good
            # assumption to make, but it's the only hint robot gives
            # me that it might be a resource file
            return ResourceFile(source)

if __name__ == "__main__":
    '''It might be nice to be able to do something like

    python -m rwb.lint --ignore RequireTagsRule mytest.txt
    -or-
    python -m rwb.lint --warn RequireTagsRule --error RequireDocRule
    -or even-
    python -m rwb.lint -w RequireTagsRule,RequireDocRule mytest.txt
    '''

    app = RobotLintApp()
    app.mainloop()



