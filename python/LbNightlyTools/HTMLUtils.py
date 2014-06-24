###############################################################################
# (c) Copyright 2013 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
'''
Common utility functions.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import re
import cgi


HTML_STYLE = '''
.xterm-style-0 {}
.xterm-style-1 {font-weight: bold}
.xterm-style-4 {text-decoration: underline}
.xterm-style-5 {font-weight: blink}
.xterm-style-7 {} # reverse
.xterm-color-0 {color: black;}
.xterm-color-1 {color: red;}
.xterm-color-2 {color: green;}
.xterm-color-3 {color: yellow;}
.xterm-color-4 {color: blue;}
.xterm-color-5 {color: magenta;}
.xterm-color-6 {color: cyan;}
.xterm-color-7 {color: white;}
.xterm-bgcolor-0 {/*background-color: black;*/}
.xterm-bgcolor-1 {background-color: red;}
.xterm-bgcolor-2 {background-color: green;}
.xterm-bgcolor-3 {background-color: yellow;}
.xterm-bgcolor-4 {background-color: blue;}
.xterm-bgcolor-5 {background-color: magenta;}
.xterm-bgcolor-6 {background-color: cyan;}
.xterm-bgcolor-7 {background-color: white;}
.even {font-family: monospace; white-space: pre-wrap;
       margin: 1pt;
       background-color: WhiteSmoke;}
.odd {font-family: monospace; white-space: pre-wrap;
       margin: 1pt;
       background-color: white;}
.stderr {background-color: PapayaWhip; font-style: italic;}
.stderr .even {font-family: monospace; white-space: pre-wrap;
               background-color: Bisque;}
.stderr .odd {font-family: monospace; white-space: pre-wrap;
              background-color: PapayaWhip;}
:target {border: solid; border-width: 1pt; margin: 0pt;}
'''


class XTerm2HTML(object):
    '''
    Class to translate an ASCII string (containing ANSI color codes), into an
    HTML page.
    
    Usage:
    
    >>> input = '\\x1b[31mHello \\x1b[34mcolored \\x1b[32mworld\\x1b[0m!'
    >>> conv = XTerm2HTML()
    >>> html = ''.join([conv.head(title='Hi!'), conv.process(input),
    ...                 conv.tail()])
    '''
    
    # cached regular expression to find ANSI color codes
    COLCODE_RE = re.compile('\x1b\\[([0-9;]*)m')

    def __init__(self, first_line=1):
        '''
        Initialize the conversion instance.
        An optional first_line can be provided if the output of the processing
        is meant to be concatenated with the output of another call to this
        class.
        '''
        self.current_code = (0, 0, 0)
        self.line = first_line - 1

    def parse_code(self, code):
        '''
        Convert the ANSI style string into a 3-tuple of text style attributes
        ids (style, color and background).
        
        >>> conv = XTerm2HTML()
        >>> conv.parse_code('0')
        (0, 0, 0)
        >>> conv.parse_code('1;34')
        (1, 4, None)
        >>> conv.parse_code('40')
        (None, None, 0)
        '''
        # Constants
        STYLE_IDX = 0
        COLOR_IDX = 1
        BGCOLOR_IDX = 2
        newcode = [None, None, None]
        for subcode in [int(x, 10) for x in code.split(';')]:
            if subcode >= 40:
                newcode[BGCOLOR_IDX] = subcode - 40
            elif subcode >= 30:
                newcode[COLOR_IDX] = subcode - 30
            else:
                newcode[STYLE_IDX] = subcode
        if newcode == [0, None, None]:  # special case
            newcode = [0, 0, 0]
        return tuple(newcode)

    def set_style(self, new_style_code):
        '''
        Set the current text style, returning True if there was a change, False
        if the new style is the same as the old one.
        
        >>> conv = XTerm2HTML()
        >>> conv.set_style('1;32;43')
        True
        >>> conv.set_style('1')
        False
        >>> conv.set_style('0;30')
        True
        '''
        new_style_code = self.parse_code(new_style_code)
        old = self.current_code
        self.current_code = [o if n is None else n
                             for n, o in zip(new_style_code, self.current_code)]
        return old != self.current_code

    @property
    def current_class(self):
        '''
        CSS class(es) for the current text style.
        '''
        if self.current_code == (0, 0, 0):
            return ''
        return ' '.join('xterm-%s-%d' % x
                        for x in zip(['style', 'color', 'bgcolor'],
                                     self.current_code))

    def head(self, title=''):
        '''
        Return a string containing the head of the HTML page.
        '''
        return ('<html><head><style>{}</style>'
                '<title>{}</title></head><body>\n').format(HTML_STYLE, title)
    
    def tail(self):
        '''
        Return a string containing the tail of the HTML page.
        '''
        return '</body></html>\n'
    
    def process(self, chunk):
        '''
        Process a chunk of text and return the corresponding HTML code.
        '''
        colcode = self.COLCODE_RE
        line_styles = ('even', 'odd')

        data = []
        for self.line, line in enumerate(chunk.splitlines(), self.line + 1):
            data.append('<div class="{}" id="l{}">'
                          .format(line_styles[self.line % 2], self.line))
            data.append('<span class="{}">'.format(self.current_class))

            pos = 0
            m = colcode.search(line)
            while m:
                data.append(cgi.escape(line[pos:m.start()], quote=True))
                if self.set_style(m.group(1)):
                    data.append('</span><span class="{}">'
                                  .format(self.current_class))
                pos = m.end()
                m = colcode.search(line, pos)
            if pos < len(line):
                data.append(cgi.escape(line[pos:], quote=True))
            data.append('</span></div>\n')
        return ''.join(data)

