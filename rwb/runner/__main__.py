import sys
import rwb
from app import RunnerApp

try:
    rwb.app = RunnerApp()
    rwb.app.mainloop()
except KeyboardInterrupt:
    print "program quit at request of the user"
    sys.exit(0)




