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
import collections
import logging

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
       border: 1pt solid WhiteSmoke;
       background-color: WhiteSmoke;}
.odd {font-family: monospace; white-space: pre-wrap;
       border: 1pt solid white;
       background-color: white;}
.stderr {background-color: PapayaWhip; font-style: italic;}
.stderr .even {font-family: monospace; white-space: pre-wrap;
               border-color: Bisque;
               background-color: Bisque;}
.stderr .odd {font-family: monospace; white-space: pre-wrap;
              border-color: PapayaWhip;
              background-color: PapayaWhip;}
:target {border-color: black;}
.stderr :target {border-color: red;}
'''


# cached regular expression to find ANSI color codes
COLCODE_RE = re.compile('\x1b\\[([0-9;]*)m')

ANSIStyle = collections.namedtuple('ANSIStyle', ['style', 'color', 'bgcolor'])
ANSIStyle.items = lambda self: self._asdict().items()

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

    def __init__(self, first_line=1):
        '''
        Initialize the conversion instance.
        An optional first_line can be provided if the output of the processing
        is meant to be concatenated with the output of another call to this
        class.
        '''
        self.current_code = ANSIStyle(0, 0, 0)
        self.line = first_line - 1
        self.log = logging.getLogger(self.__class__.__name__)

    def parse_code(self, code):
        '''
        Convert the ANSI style string into a 3-tuple of text style attributes
        ids (style, color and background).

        >>> conv = XTerm2HTML()
        >>> conv.parse_code('0')
        ANSIStyle(style=0, color=0, bgcolor=0)
        >>> conv.parse_code('1;34')
        ANSIStyle(style=1, color=4, bgcolor=None)
        >>> conv.parse_code('45')
        ANSIStyle(style=None, color=None, bgcolor=5)
        '''
        style = color = bgcolor = None
        if code:
            for subcode in [int(x, 10) for x in code.split(';')]:
                if subcode >= 40:
                    bgcolor = subcode - 40
                elif subcode >= 30:
                    color = subcode - 30
                else:
                    style = subcode

            if (style, color, bgcolor) == (0, None, None):  # special case
                color = bgcolor = 0
        return ANSIStyle(style, color, bgcolor)

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
        old_code = self.current_code
        new_code = [o if n is None else n
                    for n, o in zip(new_style_code, self.current_code)]
        self.current_code = ANSIStyle(*new_code)
        return old_code != self.current_code

    @property
    def current_class(self):
        '''
        CSS class(es) for the current text style.

        >>> conv = XTerm2HTML()
        >>> conv.set_style('1;32;43')
        True
        >>> conv.current_class
        'xterm-style-1 xterm-color-2 xterm-bgcolor-3'
        '''
        if self.current_code == ANSIStyle(0, 0, 0):
            return ''
        return ' '.join('xterm-%s-%d' % x
                        for x in self.current_code.items())

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
        self.log.debug('processing...')

        line_styles = ('even', 'odd')

        data = []
        for self.line, line in enumerate(chunk.splitlines(), self.line + 1):
            old_class = self.current_class
            data.append('<div class="{}" id="l{}">'
                          .format(line_styles[self.line % 2], self.line))

            self.log.debug('line %d: initial class %s', self.line, old_class)

            pos = 0
            while True:
                # look for a control sequence
                m = COLCODE_RE.search(line, pos)
                # we need to add the text if we fond one or there is none until
                # end of line
                if (m and pos != m.start()) or pos < len(line):
                    start = m.start() if m else len(line)
                    new_class = self.current_class
                    # trigger the class switch only if there is a change of
                    # class (new_class != old_class) and there is some text
                    # (pos != start)
                    if pos != start and new_class != old_class:
                        self.log.debug('class changed from %r to %r', old_class, new_class)
                        if old_class:
                            data.append('</span>')
                        if new_class:
                            data.append('<span class="{}">'.format(new_class))
                        old_class = new_class
                    # flush text
                    data.append(cgi.escape(line[pos:start], quote=True))

                if m:
                    # update current style
                    self.set_style(m.group(1))
                    # and set where we start looking for the next change
                    pos = m.end()
                else:
                    # eol hit
                    break
            if old_class:
                data.append('</span>')
            data.append('</div>\n')
        return ''.join(data)

# tests for special cases
def test_special_cases():
    '''Test for Special Cases'''
    assert XTerm2HTML().parse_code('') == ANSIStyle(None, None, None)
    expected = ('<div class="odd" id="l1">'
                '<span class="xterm-style-0 xterm-color-4 '
                'xterm-bgcolor-0">test</span>'
                '<span class="xterm-style-0 xterm-color-2 '
                'xterm-bgcolor-3">blah</span>'
                'blah</div>\n')
    actual = XTerm2HTML().process('\x1b[31m\x1b[34mtest'
                                  '\x1b[34;43m\x1b[32mblah\x1b[0mblah')
    print 'actual   ->', repr(actual)
    print 'expected ->', repr(expected)
    assert actual == expected
