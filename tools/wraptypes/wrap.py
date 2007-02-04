#!/usr/bin/env python

'''Generate a Python ctypes wrapper file for a header file.

Usage example::
    wrap.py -lGL -oGL.py /usr/include/GL/gl.h

    >>> from GL import *

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypesparser import *
import textwrap

class CtypesWrapper(CtypesParser):
    def __init__(self, library, file):
        super(CtypesWrapper, self).__init__()
        self.library = library
        self.file = file
        self.all_names = []
        self.known_types = {}

    def wrap(self, filename, source=None):
        self.filename = filename
        self.print_preamble()
        self.parse(filename, source)
        self.print_epilogue()

    def does_emit(self, symbol, filename):
        return filename == self.filename

    def print_preamble(self):
        import textwrap
        import time
        print >> self.file, textwrap.dedent("""
            '''Wrapper for %(library)s
            
            Generated %(date)s by %(class)s.  
            Do not modify this file.
            '''

            __docformat__ =  'restructuredtext'
            __version__ = '$Id$'

            import ctypes
            from ctypes import *
            from ctypes.util import find_library as _find_library

            _libpath = _find_library(%(library)r)
            if not _libpath:
                raise ImportError('Could not locate %(library)s library')
            _lib = cdll.LoadLibrary(_libpath)

            _int_types = (c_int16, c_int32)
            if hasattr(ctypes, 'c_int64'):
                # Some builds of ctypes apparently do not have c_int64
                # defined; it's a pretty good bet that these builds do not
                # have 64-bit pointers.
                _int_types += (ctypes.c_int64,)
            for t in _int_types:
                if sizeof(t) == sizeof(c_size_t):
                    c_ptrdiff_t = t
        """ % {
            'library': self.library,
            'date': time.ctime(),
            'class': self.__class__.__name__,
        }).lstrip()

    def print_epilogue(self):
        print >> self.file
        print >> self.file,  '\n'.join(textwrap.wrap(
            '__all__ = [%s]' % ', '.join([repr(n) for n in self.all_names]),
            width=78,
            break_long_words=False))

    def handle_ctypes_constant(self, name, value, filename, lineno):
        if self.does_emit(name, filename):
            print >> self.file, '%s = %r' % (name, value),
            print >> self.file, '\t# %s:%d' % (filename, lineno)
            self.all_names.append(name)

    def handle_ctypes_type_definition(self, name, ctype, filename, lineno):
        if self.does_emit(name, filename):
            self.all_names.append(name)
            self.emit_type(ctype)
            print >> self.file, '%s = %s' % (name, str(ctype)),
            print >> self.file, '\t# %s:%d' % (filename, lineno)
        else:
            self.known_types[name] = (ctype, filename, lineno)

    def emit_type(self, t):
        for s in t.get_required_type_names():
            if s in self.known_types:
                s_ctype, s_filename, s_lineno = self.known_types[s]
                self.emit_type(s_ctype)
               
                print >> self.file, '%s = %s' % (s, str(s_ctype)),
                print >> self.file, '\t# %s:%d' % (s_filename, s_lineno)
                del self.known_types[s]

    def handle_ctypes_function(self, name, restype, argtypes, filename, lineno):
        if self.does_emit(name, filename):
            # Also emit any types this func requires that haven't yet been
            # written.
            self.emit_type(restype)
            for a in argtypes:
                self.emit_type(a)

            self.all_names.append(name)
            print >> self.file, '# %s:%d' % (filename, lineno)
            print >> self.file, '%s = _lib.%s' % (name, name)
            print >> self.file, '%s.restype = %s' % (name, str(restype))
            print >> self.file, '%s.argtypes = [%s]' % \
                (name, ', '.join([str(a) for a in argtypes])) 
            print >> self.file

    def handle_ctypes_variable(self, name, ctype, filename, lineno):
        # This doesn't work.
        #self.all_names.append(name)
        #print >> self.file, '%s = %s.indll(_lib, %r)' % \
        #    (name, str(ctype), name)
        pass

if __name__ == '__main__':
    import optparse
    import sys
    import os.path

    usage = 'usage: %prog [options] <header.h>'
    op = optparse.OptionParser(usage=usage)
    op.add_option('-o', '--output', dest='output',
                  help='write wrapper to FILE', metavar='FILE')
    op.add_option('-l', '--library', dest='library',
                  help='link to LIBRARY', metavar='LIBRARY')
    op.add_option('-I', '--include-dir', action='append', dest='include_dirs',
                  help='add DIR to include search path', metavar='DIR',
                  default=[])
    
    (options, args) = op.parse_args()
    if len(args) < 1:
        print >> sys.stderr, 'No header file specified.'
        sys.exit(1)
    header = args[0]

    if options.library is None:
        options.library = os.path.splitext(header)[0]
    if options.output is None:
        options.output = '%s.py' % options.library

    wrapper = CtypesWrapper(options.library, open(options.output, 'w'))
    wrapper.preprocessor_parser.include_path += options.include_dirs
    wrapper.wrap(header)

    print 'Wrapped to %s' % options.output