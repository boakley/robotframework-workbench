import sys
from app import KwBrowserApp
import rwb

try:
    rwb.app = KwBrowserApp()
    rwb.app.mainloop()
except KeyboardInterrupt:
    print "program quit at request of the user"
    sys.exit(0)

