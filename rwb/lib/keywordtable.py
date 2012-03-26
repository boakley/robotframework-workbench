'''keywordtable - an SQLite database of keywords

Keywords can be loaded from resource files, test suite files,
and libdoc-formatted xml, or from python libraries
'''

import sqlite3
import os
import xml.etree.ElementTree as ET
from robot.parsing.model import ResourceFile, TestCaseFile
from robot.running import TestLibrary
from robot.errors import DataError
import time

class KeywordTable(object):
    '''A SQLite database of keywords'''
    def __init__(self, dbfile=":memory:"):
        self.db = sqlite3.connect(dbfile)
        self._init_db()

    def get_collections(self, pattern=None):
        '''Returns a list of collection name/id tuples'''
        if pattern is None:
            sql = '''SELECT collection.name, collection.id
                     FROM collection_table as collection
                  '''                
            cursor = self.execute(sql)
            sql_result = cursor.fetchall()

        else:
            sql = '''SELECT collection.name, collection.id
                     FROM collection_table as collection
                     WHERE name like ?
                  '''                
            cursor = self.execute(sql, (pattern,))
            sql_result = cursor.fetchall()

        return sql_result

    def get_keywords(self, pattern="%", longnames= False):
        '''Returns all keywords that match a SQL pattern

        If longnames is true, it returns results in the form
        "library_name.keyword_name". Library_name is not considered
        when matching the pattern. 

        The pattern matching is insensitive to case.
        '''

        if longnames:
            sql = '''SELECT collection.name, keyword.name
                     FROM collection_table as collection
                     JOIN keyword_table as keyword
                     WHERE collection.id == keyword.collection_id
                     AND keyword.name like ?
                 '''
            cursor = self.execute(sql, (pattern,))
            result = ["%s.%s" % row for row in cursor.fetchall()]
            return list(set(result))
        else:
            sql = '''SELECT name FROM keyword_table WHERE name like ?'''
            cursor = self.execute(sql, (pattern,))
            result = [row[0] for row in cursor.fetchall()]
            return list(set(result))
            
    def reset(self):
        self.execute("DELETE FROM collection_table")
        self.execute("DELETE FROM keyword_table")

    def add_directory(self, dirname):
        '''Adds all the .xml files in the given directory'''
        for filename in os.listdir(dirname):
            (name, ext) = os.path.splitext(filename)
            if ext.lower() in (".xml"):
                path = os.path.join(dirname, filename)
                self.add_file(path)

    def add_file(self, filename):
        '''Add a file to the table

        If the suffix is ".xml" it will assume it's a libdoc-formatted
        file. Otherwise it will try to load the file as if it were a
        resource file. If that fails, try to open it as a test suite file.
        '''

        (name, ext) = os.path.splitext(filename)

        if ext.lower() in (".txt", ".tsv", ".html"):
            try:
                self.add_resource_file(filename)
            except DataError, e:
                # not a resource file. Maybe it's a test file
                try:
                    self.add_testsuite_file(filename)
                except DataError, e:
                    raise DataError("%s: not a resource or test sutie file" % filename)

        elif ext.lower() in (".xml"):
            self.add_libdoc_file(filename)
            
        else:
            raise DataError("%s: unsupported file type" % filename)

    def add_library(self, name, *args):
        lib = TestLibrary(name, args)
        namedargs = "yes" if len(lib.named_args) > 0 else "no"

        if len(lib.handlers) > 0:
            collection_id = self.add_collection(lib.name, "library",
                                                lib.doc, lib.version,
                                                lib.scope, namedargs)
            for handler in lib.handlers.values():
                self._add_keyword(collection_id, handler.name, handler.doc, handler.arguments.names)

    def add_testsuite_file(self, filename):
        '''Add all keywords in a test suite file'''
        suite = TestCaseFile(self, source=filename)
        suite.populate()
        if len(suite.keywords) > 0:
            collection_id = self.add_collection(suite.name, "testsuite",suite.setting_table.doc.value) 

            for kw in suite.keywords:
                args = [arg.strip("${}") for arg in kw.args.value]
                self._add_keyword(collection_id, kw.name, kw.doc.value, args)
        
    def add_resource_file(self, filename):
        '''add all keywords in a resource file'''
        resource = ResourceFile(source=filename)
        resource.populate()

        if len(resource.keywords) > 0:
            collection_id = self.add_collection(resource.name, "resource", 
                                                resource.setting_table.doc.value)
            for kw in resource.keywords:
                args = [arg.strip("${}") for arg in kw.args.value]
                self._add_keyword(collection_id, kw.name, kw.doc.value, args)

    def add_libdoc_file(self, filename):
        '''add all keywords from a libdoc-generated xml file'''
        tree = ET.parse(filename)
        root = tree.getroot()
        if root.tag != "keywordspec":
            raise Exception("expect root tag 'keywordspec', got '%s'" % root.tag)

        collection_id = self.add_collection(root.get("name"), root.get("type"),
                                             root.get("doc"), root.get("version"),
                                             root.get("scope"), root.get("namedargs"))
        for kw in tree.findall("kw"):
            kw_name = kw.get("name")
            kw_doc = _get_text(kw, "doc")
            args_element = kw.find("arguments")
            kw_args = []
            if args_element is not None:
                for arg_element in args_element.findall("arg"):
                    kw_args.append(arg_element.text)
            self._add_keyword(collection_id, kw_name, kw_doc, kw_args)

    def execute(self, *args):
        '''Execute an SQL query'''
        cursor = self.db.cursor()
        cursor.execute(*args)
        return cursor

    def add_collection(self, c_name, c_type, c_doc, c_version="unknown", c_scope="", c_namedargs="yes"):
        '''Insert data into the collection table'''
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO collection_table 
                (name, type, version, scope, namedargs, doc)
            VALUES 
                (?,?,?,?,?,?)
        ''', (c_name, c_type, c_version, c_scope, c_namedargs, c_doc))
        collection_id = cursor.lastrowid
        return collection_id
        
    def _add_keyword(self, collection_id, name, doc, args):
        '''Insert data into the keyword table
        
        'args' should be a list, but since we can't store a list in an
        sqlite database we'll make it pipe-separated. I chose that
        because that's how RIDE's keyword tool presents arguments and
        I'm shooting for feature parity. Plus, space-pipe-space is
        pretty easy to parse if we want to convert it back to a list.
        '''
        argstring = " | ".join(args)
        self.db.execute('''
            INSERT OR REPLACE INTO keyword_table 
                (collection_id, name, doc, args)
            VALUES 
                (?,?,?,?)
        ''', (collection_id, name, doc, argstring))

    def _init_db(self):
        
        cursor = self.db.execute('''
            SELECT name FROM  sqlite_master 
            WHERE type='table' AND name='collection_table'
        ''')
        if len(cursor.fetchall()) == 0:
            self.db.execute('''
                CREATE TABLE collection_table
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 name TEXT COLLATE NOCASE UNIQUE, 
                 type COLLATE NOCASE,
                 version TEXT,
                 scope TEXT,
                 namedargs TEXT,
                 doc TEXT)
            ''')
            self.db.execute('''
                CREATE INDEX collection_index
                ON collection_table (name)
            ''')

        cursor = self.db.execute('''
            SELECT name FROM  sqlite_master 
            WHERE type='table' AND name='keyword_table'
        ''')

        if len(cursor.fetchall()) == 0:
            self.db.execute('''
                CREATE TABLE keyword_table
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT COLLATE NOCASE, 
                 collection_id INTEGER,
                 doc TEXT, 
                 args text)
            ''')
            self.db.execute('''
                CREATE INDEX keyword_index
                ON keyword_table (name)
            ''')


def _get_text(rootElement, childName):
    '''Helper function to get the text of an ElementTree element

    This returns an empty string if the tag has no text.
    '''
    element = rootElement.find(childName)
    if element is not None and element.text is not None:
        return element.text
    return ""

if __name__ == "__main__":
    '''Run this like "python keywordtable.py keywords.txt"
    You can also give a directory with .xml files as an 
    argument, and even robot test suite files.
    '''
    import sys
    kwdb = KeywordTable()
    for path in sys.argv[1:]:
        if os.path.isdir(path):
            kwdb.add_directory(path)
        else:
            kwdb.add_file(path)

    sql = '''SELECT collection.name, keyword.name, keyword.args
             FROM collection_table as collection
             JOIN keyword_table as keyword
             WHERE collection.id == keyword.collection_id
             AND keyword.name like ?
         '''
    cursor = kwdb.execute(sql, ("%",))
    result = ["%s.%s / %s" % row for row in cursor.fetchall()]
    for r in result:
        print "=>", r

    print "collections:", kwdb.get_collections()
