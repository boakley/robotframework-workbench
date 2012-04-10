import rwb
from app import EditorApp
try:
    rwb.app = EditorApp()
    rwb.app.mainloop()
except KeyboardInterrupt:
    print "program quit at request of the user"
    pass
