#!/usr/bin/env python

''' UNTESTED !!!  (but seems to work)

run 'python setup.py bdist', then 'python dist/debugger-*.zip'

'''

import os
import sys
from distutils.core import setup
from distutils.command.bdist_dumb import bdist_dumb
import app
import rwb

# see http://stackoverflow.com/a/6195072/7432
class custom_bdist_dumb(bdist_dumb):
    def reinitialize_command(self, name, **kw):
        cmd = bdist_dumb.reinitialize_command(self, name, **kw)
        if name == 'install':
            cmd.install_lib = '\\'
        return cmd

setup(name             = app.NAME,
      cmdclass         = {'bdist_dumb': custom_bdist_dumb},
      description      = app.__doc__.split("\n",1)[0],
      version          = rwb.__version__,
      author           = 'Bryan Oakley',
      author_email     = 'bryan.oakley@gmail.com',
      keywords         = 'robotframework testing testautomation',
      classifiers      = [
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
        "Intended Audience :: Developers",
        ],
      package_dir = {'': '.',
                     'rwb': '..',
                     },
      packages = ['rwb.lib',
                  'rwb.runner',
                  'rwb.misc',
                  'rwb.widgets',
                  'rwb.images',
                  'rwb.editor',
                  ],
      py_modules = ['__main__', '__init__', 
                    'keyworddte', 
                    'app', 'varlist', 
                    ],
      )

