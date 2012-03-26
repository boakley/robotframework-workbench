'''listener.py

This implements the classes used as the endpoint of a SocketListener
(see socket_listener.py). 

RemoteRobotListener is the class that should be instantiated to listen
for results from the SocketListener. 

'''

import SocketServer
import StringIO
import Tkinter as tk
import json

class RemoteRobotListener(tk.Frame):
    '''A Robot Framework listener that listens over a socket

    This creates an event-based socket server that listens for
    listener events sent to it from a robot test running in 
    another process (and potentially on another machine).

    This uses the Tkinter socket code and fileevents because
    they are much easier to work with than python threads. 

    Inputs:

    root     - a tkinter root window
    callback - a function to be called for each message from a running robot test

    '''
    def __init__(self, parent, callback, port=0):
        self._parent = parent
        self.callback = callback
        tk.Frame.__init__(self, parent)
        self.bind("<Destroy>", self._on_destroy)

        # this creates a tcl command named "socket_callback" which 
        # is a proxy for our python method named "callback_proxy"
        parent.createcommand("socket_callback", self.callback_proxy)

        # This runs some Tcl code to establish a socket server. 
        # the code returns the port that the server is running on.
        self.port = parent.eval('''
            proc Server {channel addr port} {
                fileevent $channel readable [list readline $channel]
            }
            proc readline {channel} {
                if {[gets $channel line] == -1} {
                    fileevent $channel readable {}
                    close $channel
                } else {
                    socket_callback $line
                }
            }
            set ::the_socket [socket -server Server 0]
            set port [lindex [fconfigure $::the_socket -sockname] end]
        ''')

    def callback_proxy(self, data):
        '''Deserialize the data and pass it to the callback

        This is called whenever data arrives on the socket.
        '''
        try:
            self.callback(*json.loads(data))
        except Exception, e:
            print "%s.callback_proxy(): WTF?" % __file__, e
            import traceback
            traceback.print_exc()
            foo = traceback.format_exc()
            print "really, WTF?", foo


    def _on_destroy(self, event):
        '''Called when this object is destroyed

        This stops the socket server. 
        '''
        self._parent.eval('''
            # Without making a quick connection to the server, the
            # program will hang. 
            catch {
                set sock [socket localhost %s]
                # close $foo
                close $::the_socket
            }
       ''' % self.port)

