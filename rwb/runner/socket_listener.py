'''A Robot Framework listener that sends information to a socket in JSON format

This requires Python 2.6+
'''

import os
import socket
import sys
import json

PORT = 5007
HOST = "localhost"

# Robot expects the class to be the same as the filename, so
# we can't use the convention of capitalizing the class name
class socket_listener:
    """Pass all listener events to a remote listener

    If called with one argument, that argument is a port
    If called with two, the first is a hostname, the second is a port
    """
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, *args):
        self.port = PORT
        self.host = HOST
        self.sock = None
        if len(args) == 1:
            self.port = int(args[0])
        elif len(args) >= 2:
            self.host = args[0]
            self.port = int(args[1])
        self._connect()
        self._send_pid()

    def _send_pid(self):
        self._send_socket("pid", os.getpid())

    def start_test(self, name, attrs):
        self._send_socket("start_test", name, attrs)

    def end_test(self, name, attrs):
        self._send_socket("end_test", name, attrs)

    def start_suite(self, name, attrs):
        self._send_socket("start_suite", name, attrs)

    def end_suite(self, name, attrs):
        self._send_socket("end_suite", name, attrs)

    def start_keyword(self, name, attrs):
        self._send_socket("start_keyword", name, attrs)

    def end_keyword(self, name, attrs):
        self._send_socket("end_keyword", name, attrs)

    def message(self, message):
        self._send_socket("message", message)

    def log_message(self, message):
        self._send_socket("log_message", message)

    def log_file(self, path):
        self._send_socket("log_file", path)

    def output_file(self, path):
        self._send_socket("output_file", path)

    def report_file(self, path):
        self._send_socket("report_file", path)

    def summary_file(self, path):
        self._send_socket("summary_file", path)

    def debug_file(self, path):
        self._send_socket("debug_file", path)

    def close(self):
        self._send_socket("close")
        if self.sock:
            self.filehandler.close()
            self.sock.close()

    def _connect(self):
        '''Establish a connection for sending pickles'''
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.filehandler = self.sock.makefile('w')
        except socket.error, e:
            print 'unable to open socket to "%s:%s" error: %s' % (self.host, self.port, str(e))
            self.sock = None

    def _send_socket(self, name, *args):
        if self.sock:
            packet = json.dumps([name,] + list(args)) + "\n"
            self.filehandler.write(packet)
            self.filehandler.flush()

