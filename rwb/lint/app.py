import logging
import sys
from robot.parsing.model import TestData
from lint import RobotChecker ;# rename this to LintController?

class RobotLintApp(object):
    def __init__(self):
        self.checker = RobotChecker()

    def mainloop(self):
        for path in sys.argv[1:]:
            suite = TestData(parent=None, source=sys.argv[1])
            self.checker.check(suite)
        
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



