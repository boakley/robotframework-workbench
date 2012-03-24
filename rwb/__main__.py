import sys
import os
import runpy

'''
Standard usage is one of these:

python -m rwb.editor <args>
python -m rwb.runner <args>
python -m rwb.kwbrowser <args>

You can also run the "rwb" module directly, which will simply run the editor
'''
if len(sys.argv) > 1 and sys.argv[1] in ("editor", "runner", "kwbrowser"):
    PKG = "rwb." + sys.argv.pop(1)
else:
    # from the command line, let "rwb" be an alias for "rwb editor"
    PKG = "rwb.editor"

# This code came from this page:
# http://code.activestate.com/recipes/577088-generic-execution-script-for-a-packageapplication/
try:
    run_globals = runpy.run_module(PKG, run_name='__main__', alter_sys=True)
    executed = os.path.splitext(os.path.basename(run_globals['__file__']))[0]
    if executed != '__main__':  # For Python 2.5 compatibility
        raise ImportError('Incorrectly executed %s instead of __main__' %
                            executed)
except ImportError:  # For Python 2.6 compatibility
    runpy.run_module('%s.__main__' % PKG, run_name='__main__', alter_sys=True)
