import os.path

'''FIXME:

Prefix messages with [w] for warning, [e] for error. Maybe others? 
pylint uses (c) for convention, (r) refactor / bad code smell
'''


WARNING="[w]"
ERROR="[e]"

class Rule(object): 
    level = WARNING
    # the idea is that the user can use a command line argument to
    # ignore certain rules; the caller can then do 'rule.ignore=True'
    # to cause a rule to be ignored. Not implemented yet.
    ignore = False
    def warn(self, obj, message):
        source = os.path.basename(getattr(obj,"source", "?"))
        longname = getattr(obj,"longname", getattr(obj,"name", str(obj)))
        print("%s %s:%s: %s" % (self.level, source, longname, message))

# these exist so that the checker can find all rules that
# pertain only to test cases, or only pertain to test suites
class TestCaseRule(Rule): pass
class TestSuiteRule(Rule): pass
#class ResourceFileRule(Rule): pass

#class RequireResourceDocs(ResourceFileRule):
#    pass

class RequireTagsRule(TestCaseRule):
    '''Verify that there is at least one tag associated with the test case'''
    def __call__(self, testcase):
        if testcase.tags is None or testcase.tags.value is None or len(testcase.tags.value) == 0:
            self.warn(testcase, "testcase does not have a [Tag] section")

class RequireDocRule(TestCaseRule, TestSuiteRule):
    '''Verify that a test case or suite has documentation'''
    def __call__(self, testcase):
        doc = testcase.__doc__
        if doc is None or len(doc.strip()) == 0:
            self.warn(testcase, "there is no [Documentation] section")
#            logging.warn("%s: missing documentation" % testcase.longname)

class TagNameNoSpace(TestCaseRule):
    '''Verify that tag names don't include spaces'''
    def __call__(self, testcase):
        if testcase.tags is not None and testcase.tags.value is not None:
            for tag in testcase.tags.value:
                if " " in tag.strip():
                    self.warn(testcase, "tag should not contain spaces: '%s'" % (tag,))

