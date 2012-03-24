import app
try:
    app = app.EditorApp()
    app.mainloop()
except KeyboardInterrupt:
    print "program quit at request of the user"
    pass
