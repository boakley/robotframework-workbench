'''
'''

from listener import RemoteRobotListener
from tsubprocess import Process
import shlex
import logging
import os

class RobotController(object):
    '''A class for controlling the execution of a robot test
    
    This class does *not* run the test; that is done in a separate
    process. What this class does is monitor the output, and acts
    as a listener (listening to the running test via a socket). 

    Special GUI listeners may be associated with this controller.
    Each message that comes back from the running robot test is
    forwarded to each of these GUI listeners. 

    These listeners must provide a "listen" method which accepts an
    id, an event name (one of the supported robot listener messages
    such as 'start_suite', 'start_test', etc), and then zero or more
    additional arguments.

    '''
    def __init__(self, parent, runner="python -m robot.runner"):
        self._parent = parent
        self._listener = RemoteRobotListener(parent, self._listen)
        self._port = self._listener.port
        self._poll_job_id = None
        self._process = None
        self._listeners = []
        self._args = []
        self._cwd = os.getcwd()
        self._runner = runner

        # every event gets an id, a simple incrementing integer. The plan
        # is that each display (console, log, etc) will be able to jump
        # to the related item in some other display using this id (ie:
        # from the message window you can jump to the details window or
        # visa versa) (this isn't implemented yet...)
        #
        # (of course, most events have timestamps that could serve
        # the same purpose... need to think harder about this some day)
        self._id = 0

    def __del__(self):
        try:
            if self._poll_job_id is not None:
                self.after_cancel(self._poll_job_id)
        except:
            pass

    def configure(self, args=None, listeners=None, runner=None, cwd=None):
        '''Configure the runner
        args - the arguments to pass to the runner
        listeners - a list of listeners (actually, MVC views)
        runner - the command to start a test run
        '''
        if args is not None: self._args = args
        if listeners is not None: self._listeners = listeners
        if runner is not None: self._runner = runner
        if cwd is not None: self._cwd = cwd

    def start(self):
        '''Start the test process
        '''
        if self._process:
            raise Exception("there is already a running process")

        for listener in self._listeners:
            listener.reset()

        here = os.path.abspath(os.path.dirname(__file__))
        socket_listener = os.path.join(here, "socket_listener.py:%s" % self._port)

        full_args = ["--listener", socket_listener, "--log", "NONE", 
                     "--report", "NONE"] + self._args
        cmd = shlex.split(self._runner) + full_args
        logging.debug("command: " + " ".join(cmd))

        self._process = Process(cmd, cwd=self._cwd)
        self._listen("start_job", cmd)
        if self._poll_job_id is not None:
            self._parent.after_cancel(self._poll_job_id)
            self._poll_job_id = None
        self.poll(100)

    def poll(self, delay):
        '''Poll the running process for data on stdout and stderr'''
        if self._process:
            (stdout, stderr) = self._process.read()

            if stdout: self._listen("stdout", stdout)
            if stderr: self._listen("stderr", stderr)

            if self._process.exit_code() is not None:
                # It's dead, Jim.
                self._listen("stop_job", self._process.exit_code())
                del self._process
                self._process = None

            self._poll_job_id = self._parent.after(delay, self.poll, delay)

    def _listen(self, name, *args):
        '''Forward messages to each registered listener'''
        self._id += 1
        for listener in self._listeners:
            listener.listen(self._id, name, args)

    def stop(self):
        if self._process:
            self._process.terminate()

if __name__ == "__main__":
    '''Wow! See how easy it is to make a GUI with these classes!
    '''

    import Tkinter as tk
    import sys
    from log import RobotLogTree, RobotLogMessages
    from console import RobotConsole

    root = tk.Tk()
    console = RobotConsole(root, background="white")
    console.pack(side="top", fill="both", expand=True)
    log = RobotLogTree(root)
    log.pack(side="top", fill="both", expand=True)
    messages = RobotLogMessages(root)
    messages.pack(side="top", fill="both", expand=True)

    runner = RobotController(root)
    runner.configure(args=sys.argv[1:], listeners=(console,log,messages))

    root.after(1, runner.start)
    root.mainloop()
