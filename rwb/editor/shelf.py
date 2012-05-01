import ttk
import Tkinter as tk
from rwb.widgets import BottomTabNotebook
from rwb.runner import RobotConsole, RobotLogTree, RobotLogMessages, RobotController

class Shelf(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        
        notebook = BottomTabNotebook(self)
        notebook.pack(side="top", fill="both", expand=True)
        self.console = RobotConsole(notebook, background="white")
        self.log_tree = RobotLogTree(notebook)
        self.log_messages = RobotLogMessages(notebook)

        notebook.add(self.log_tree, text="Details")
        notebook.add(self.console, text="Console")
        notebook.add(self.log_messages, text="Messages")

        self.controller.configure(listeners=[self.log_tree, self.console, self.log_messages])

    def listen(self, *args):
        pass
