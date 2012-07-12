'''DebugLibrary

This keyword library contains the following keywords, useful for
debugging robot test cases:

| breakpoint | message=None

    This keyword will cause the test to block until it receives an
    xmlrpc request to either continue or exit. This keyword is
    designed to work with the rwb.debugger (robotframework workbench
    debugger) module.

'''

from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from robot.libraries.BuiltIn import BuiltIn
import robot.errors
import sys

class CustomXMLRPCServer(SimpleXMLRPCServer):
    def handle_request(self):
        self._timedout=False
        SimpleXMLRPCServer.handle_request(self)

    def handle_timeout(self):
        self._timedout=True

    def timedout(self):
        return self._timedout

class DebugLibrary(object):
    # global, so we can create a single XMLRPC server that lasts for
    # the life of the suite
    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    def __init__(self, port=8911):
        self.timeout = 5 ;# seconds
        self.server = CustomXMLRPCServer(("localhost", 0), 
                                   SimpleXMLRPCRequestHandler, 
                                   allow_none=True,
                                   logRequests=False)
        self.port = self.server.server_address[1]
        self.server.register_function(self._ping, "ping")
        self.server.register_function(self._resume, "resume")
        self.server.register_function(self._get_variables, "get_variables")
        self.server.register_function(self._stop, "stop")
        self.server.register_function(self._run_keyword, "run_keyword")
        self.server.register_function(self._fail_test, "fail_test")

    def breakpoint(self, message=None):
        # This message is intended to be interpreted by a remote
        # listener. This keyword will block until the remote listener
        # sends back a command to continue or fail (via the XMLRPC
        # methods "stop", "fail_test", "fail_suite"  or "resume"
        # "fail_suite" isn't working right now :-(
        log_message = ":break:%s:" % self.port
        if message is not None:
            log_message += " " + message
        sys.stdout.flush()
        BuiltIn().log(log_message, "DEBUG")

        # this enters into a mini event loop, handling requests
        # from the remote listener. Of course, if there is no
        # remote listener this will hang. 
        self.state = "break"
        self.server.timeout=self.timeout
        while self.state == "break":
            try:
                self.server.handle_request()
                if self.server.timedout():
                    BuiltIn().log("timeout waiting for debugger", "WARN")
                    return

                if self.state == "continue": break
                if self.state == "fail_test":
                    raise AssertionError("debug fail")

                if self.state == "fail_suite":
                    error = robot.errors.ExecutionFailed("debug quit")
                    error = AssertionError("killed by the debugger")
                    error.ROBOT_EXIT_ON_FAILURE = True
                    raise error
            except Exception, e:
                BuiltIn().log("unexpected error handling request from debugger: %s" % str(e), "DEBUG")
                raise

    def _resume(self):
        self.state = "continue"

    def _stop(self, message="stopped by debugger"):
        self.state = "fail_suite"

    def _fail_test(self, message="test failed via debugger"):
        self.state = "fail_test"

    def _run_keyword(self, *args):
        BuiltIn().log("debug: " + " ".join(args), "DEBUG")
        return BuiltIn().run_keyword(*args)

    def _get_variables(self):
        variables = BuiltIn().get_variables()
        return dict(variables)

    def _ping(self):
        return "ping"


