try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from rwb.lib.decorators import cached_property
import urllib2

class RobotLog(object):
    def __init__(self):
        self.path = None
        self.suites = []
        self.statistics = None

    def parse(self, path):
        self.path = path
        self.suites = []
        try:
            if "//" in path:
                f = urllib2.urlopen(path)
            else:
                f = open(path)
        except Exception, e:
            raise Exception("unable to open requested path: %s" % str(e))

        xml = ET.parse(f)
        root = xml.getroot()
        if root.tag != "robot":
            raise Exception("expect root tag 'robot', got '%s'" % root.tag)

        self.statistics = RobotStatistics(root.find("statistics"))
        for suite in root.findall("suite"):
            s = RobotSuite(suite)
            self.suites.append(s)

class RobotStatistics(object):
    def __init__(self, xml_object):
        self.xml_object = xml_object
        
    @cached_property
    def totals(self):
        # foo.stats["critical"]["pass"]
        total = self.xml_object.find("total")
        result = {
            "critical": {
                "pass": total.findall("stat")[0].get("pass"),
                "fail": total.findall("stat")[0].get("fail"),
                },
            "all": {
                "pass": total.findall("stat")[1].get("pass"),
                "fail": total.findall("stat")[1].get("fail"),
                }
            }
        return result
            
    @cached_property
    def stats_by_suite(self):
        # returns {"suite1": (pass, fail), "suite2": (pass, fail), etc}
        result = {}
        for suite in self.xml_object.findall("suite"):
            longname = tag.text.strip()
            result[longname] = {
                "pass": suite.get("pass"),
                "fail": suite.get("fail")
                }
        return result

    @cached_property
    def stats_by_tag(self):
        # returns {"tag1": (pass, fail), "tag2": (pass, fail), etc}
        result = {}
        for tag in self.xml_object.findall("tag"):
            longname = tag.text.strip()
            result[longname] = {
                "pass": tag.get("pass"),
                "fail": tag.get("fail")
                }
        return result


class RobotObject(object):
    '''A generic class representing an object in a robot log file (eg: output.xml)'''
    def __init__(self, xml_object, parent=None):
        self.xml_object = xml_object
        self.parent = parent

    @property
    def tostring(self):
        return ET.tostring(self.xml_object)

    @cached_property 
    def name(self):
        return self.xml_object.get("name")

    @cached_property
    def doc(self):
        return self.xml_object.find("doc").text()

    @cached_property
    def _status(self):
        return self.xml_object.find("status")

    @cached_property
    def status(self):
        return self._status.get("status")

    @cached_property
    def passed(self):
        return self.status == "PASS"

    @cached_property
    def failed(self):
        return self.status != "PASS"


    @cached_property
    def status_message(self):
        return self._status.text

    @cached_property
    def starttime(self):
        time = self._status.get("starttime").split(" ")[1]
        return time

    @cached_property
    def endtime(self):
        time = self._status.get("endtime").split(" ")[1]
        return time

class RobotMessage(RobotObject):
    @cached_property
    def level(self):
        return self.xml_object.get("level")
    @cached_property
    def starttime(self):
#        time = self.xml_object.get("timestamp").split(" ")[1]
#        return time
        return ""

    @cached_property
    def endtime(self):
        return ""
    @cached_property
    def text(self):
        return self.xml_object.text

class RobotKeyword(RobotObject):
    @cached_property
    def type(self):
        return self.xml_object.get("type")

    @cached_property
    def shortname(self):
        return self.name.rsplit(".",1)[-1]

    @cached_property
    def args(self):
        args = []
        arguments = self.xml_object.find("arguments")
        for arg in arguments.findall("arg"):
            args.append(arg.text)
        return args

    @property
    def keywords(self):
        for kw in self.xml_object.findall("kw"):
            yield RobotKeyword(kw)

    @property
    def messages(self):
        for msg in self.xml_object.findall("msg"):
            yield RobotMessage(msg)

class RobotTest(RobotObject):
    @property
    def keywords(self):
        for kw in self.xml_object.findall("kw"):
            yield RobotKeyword(kw)

class RobotSuite(RobotObject):
    @property
    def suites(self):
        for suite in self.xml_object.findall("suite"):
            yield RobotSuite(suite, parent=self)

    @property
    def keywords(self):
        '''Suite keywords, such as setup and teardown'''
        for kw in self.xml_object.findall("kw"):
            yield RobotKeyword(kw)

    @property
    def tests(self):
        for test in self.xml_object.findall("test"):
            yield RobotTest(test, parent=self)

    @cached_property
    def source(self):
        return self.xml_object.get("source")

        
