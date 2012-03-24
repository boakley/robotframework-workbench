#! /usr/bin/env python

'''Threaded subprocess library

This provides an object wrapper around a subprocess.popen call, 
with threads to cache stdout and stderr so that the caller won't
block when trying to read. 

This code requires python 2.6 or greater
'''
import os, sys
import time
import errno
import platform
import signal
import threading
import subprocess
import Queue

# Nothing magical about these values; they are just 
# names to associate with the threads. They could be
# random integers, but strings make debugging easier.
STDERR_THREAD = "stderr-thread"
STDOUT_THREAD = "stdout-thread"

class Process(object):
    """Object that represents a running process
    """

    def __init__(self, cmd, shell=False, cwd=None, env=None, 
                 universal_newlines=False, startupinfo=None, creationflags=0):

        self._quit = False
        self._stdout_queue = Queue.Queue()
        self._stderr_queue = Queue.Queue()
        self._exit_status = None
        self._lock = threading.Lock()

        if platform.system() == "Windows":
            self._process = subprocess.Popen(cmd,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             universal_newlines=True,
                                             creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            self._process = subprocess.Popen(cmd,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             universal_newlines=True)

        if self._process.stdout:
            self._stdout_thread = threading.Thread(
                name = STDOUT_THREAD,
                target = self._reader, args=(self._stdout_queue,
                                             self._process.stdout,
                                             "stdout"))
            self._stdout_thread.setDaemon(True)
            self._stdout_thread.start()

        if self._process.stderr:
            self._stderr_thread = threading.Thread(
                name = STDERR_THREAD,
                target = self._reader, args=(self._stderr_queue,
                                             self._process.stderr,
                                             "stderr"))
            self._stderr_thread.setDaemon(True)
            self._stderr_thread.start()

    def __del__(self):
        if self._exit_status is None:
            try:
                sig = getattr(signal, "SIGKILL", signal.SIGTERM)
                os.kill(self.pid(), sig)
            except Exception:
                pass

    def is_alive(self):
        '''Return True if the process is alive'''
        if self._process is None:
            return False
        else:
            poll = self._process.poll()
            return poll is None

    def exit_code(self):
        """Checks to see if the process has terminated. 
        Return None, or the process return code if it has terminated.
        """
        return self._process.poll()

    def pid(self):
        """Return the process pid
        alias to the pid method on the process
        """
        return self._process.pid

    def kill(self, sig):
        """Attempt to kill the process if it still seems to be running. """
        print "BLAM! my pid is", self.pid()
        if self._exit_status is not None:
            raise OSError(errno.ESRCH, os.strerror(errno.ESRCH))
        try:
            print "killing..."
            result = os.kill(self.pid(), sig)
            print "done killing?", result
        except OSError, e:
            # not much we can do at this point.
            print "WTF? Kill throw an error:", e

    def wait(self, flags=0):
        """Wait for the process to end

        This calls os.waitpid, and flags is passed to that function.
        If flags contains os.WNOHANG this function will return None
        (ie: not actually wait) if the process hasn't terminated.
        """
        if self._exit_status is not None:
            return self._exit_status
        pid,exit_status = os.waitpid(self.pid(), flags)
        if pid == 0:
            return None
        if os.WIFEXITED(exit_status) or os.WIFSIGNALED(exit_status):
            self._exit_status = exit_status
            if self._process.stdout:
                self._stdout_thread.join()
            if self._process.stderr:
                self._stderr_thread.join()
        return exit_status

    def terminate(self):
        print "process.terminate()... sending a signal... pid=", self._process.pid
        # this kills it dead even though robot seems to 
        # explicitly handle SIGTERM. Hmmm. 
        os.kill(self._process.pid, signal.SIGTERM)
#        self._process.kill(signal.SIGINT)
        print "done with terminate()..."

    def busted_terminate(self, timeout=.5):
        """Attempt to gracefully terminate the process """
#        self.kill(signal.SIGTERM)
        print "Sending SIGINT..."
        self.kill(signal.SIGINT)
        try:
            func = RunWithTimeout(self.wait, timeout=timeout)
            return func()
        except TimeoutException:
            pass
            
        # ok, none of the above worked. Let's pull out the big guns
        if hasattr(signal, "SIGKILL"):
            self.kill(signal.SIGKILL)
            return self.wait()

    def _reader(self, queue, source, name):
        """Read data from source and cache it, send event that data is ready"""
        while True:
            data = os.read(source.fileno(), 65536)
            if data == "":
                source.close()
                break
            else:
                queue.put(data)
        return

    def read(self):
        """Return a two-tuple of the cached data for stdout and stderr"""
        stdout = ""
        stderr = ""
        while not self._stdout_queue.empty():
            stdout += self._stdout_queue.get(block=False)
        while not self._stderr_queue.empty():
            stderr += self._stderr_queue.get(block=False)
        return (stdout, stderr)

# the following two classes (TimeoutException and RunWithTimeout) were
# inspired by this website: http://nick.vargish.org/clues/python-tricks.html 
# AFAIK there are no licensing restrictions.
class TimeoutException(Exception): 
    """Exception to raise on a timeout""" 
    pass 

class RunWithTimeout: 
    '''Create an object that runs a function with a timeout

    If the function exceeds the timeout, a TimeoutException will be thrown '''

    def __init__(self, function, timeout=.5): 
        ''''timeout' is in seconds'''
        self.timeout = timeout 
        self.function = function 

    def handle_timeout(self, signum, frame): 
        raise TimeoutException()

    def __call__(self, *args, **kwargs): 
        if hasattr(signal, "SIGALRM"):
            old = signal.signal(signal.SIGALRM, self.handle_timeout) 
            signal.alarm(self.timeout) 
            try: 
                result = self.function(*args, **kwargs)
            finally: 
                signal.signal(signal.SIGALRM, old)
            signal.alarm(0)
        else:
            result = self.function(*args, **kwargs)
        return result 

