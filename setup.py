from distutils.core import setup

import rwb

setup(
    name             ='robotframework-workbench',
    version          = rwb.__version__,
    author           ='Bryan Oakley',
    author_email     ='bryan.oakley@gmail.com',
    url              ='https://github.com/boakley/robotframework-workbench/',
    keywords         = 'robotframework testing testautomation',
    license          ='Apache License 2.0',
    description      ='Tools for working with the robotframework testing framework',
    long_description = open('README.txt').read(),
    platform         = "any",
    classifiers      = [
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
        "Intended Audience :: Developers",
        ],
    packages         =[
        'rwb', 
        'rwb.widgets', 
        'rwb.editor', 
        'rwb.runner', 
        'rwb.kwbrowser', 
        'rwb.images', 
        'rwb.lib'
        ],
    scripts          =[],
)
