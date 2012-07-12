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

class JSONSocketServer(tk.Frame):
    '''A simple event-based socket server

    This listens for messages on the socket, translates them
    from JSON, then calls the callback.

    This uses the Tkinter socket code and fileevents because
    they are (IMHO) much easier to work with than python threads. 
    It is implemented as a widget so we can work with the
    event loop, and for easy cleanup when the widget is destroyed
    (but before the python object is actually deleted)

    Inputs:

    root     - a tkinter root window
    callback - a function to be called upon receipt of a message

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
        # Sorry, but Tcl's socket handling with fileevents is 
        # superior to anything python has 
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
            set ::the_socket [socket -server Server %s]
            set port [lindex [fconfigure $::the_socket -sockname] end]
        ''' % port)

    def callback_proxy(self, data):
        '''Deserialize the data and pass it to the callback

        This is called by the underlying tcl socket mechanism
        whenever data arrives on the socket.
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

# for backwards compatibility with older code...
# (old. HA! this isn't even at version 1.0 yet!)
class RemoteRobotListener(JSONSocketServer):
    pass
