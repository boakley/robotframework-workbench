from app import RunnerApp

try:
    app = RunnerApp()
    app.mainloop()
except KeyboardInterrupt:
    print "program quit at request of the user"



