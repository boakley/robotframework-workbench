from robot.parsing.model import TestCaseFile, TestDataDirectory, TestCase, UserKeyword

from rules import TestSuiteRule, TestCaseRule

class RobotChecker(object):
        
    def check(self, suite):
        '''Run all rules against the given suite and its children'''
        for rule in TestSuiteRule.__subclasses__():
            # precompute the longname, so each rule doesn't have to
            # do it separately
            suite.longname = self._get_longname(suite)
            r = rule()
            if not r.ignore:
                r(suite)

        for testcase in suite.testcase_table:
            # precompute the longname, so each rule doesn't have to
            # do it separately
            testcase.longname = self._get_longname(testcase)
            for rule in TestCaseRule.__subclasses__():
                r = rule()
                if not r.ignore:
                    r(testcase)

    def _get_longname(self, obj):
        names = [obj.name]
        parent = obj.parent
        while parent is not None:
            if (isinstance(parent, TestCaseFile) or
                isinstance(parent, TestDataDirectory) or
                isinstance(parent, TestCase) or
                isinstance(parent, UserKeyword)):
                names.insert(0, parent.name)
            parent = parent.parent
        return ".".join(names)

