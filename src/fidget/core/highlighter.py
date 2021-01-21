from fidget.backend.QtCore import QRegExp
from fidget.backend.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter


def format(color, style=''):
    """
    Return a QTextCharFormat with the given attributes.
    """
    _color = QColor()
    _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    'keyword': format('blue'),
    'builtin': format('olive'),
    'operator': format('red'),
    'brace': format('darkGray'),
    'defclass': format('black', 'bold'),
    'string': format('magenta'),
    'string2': format('darkMagenta'),
    'comment': format('darkGreen', 'italic'),
    'self': format('black', 'italic'),
    'numbers': format('brown'),
}


class Python3Highlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for the Python language.
    """
    # Python keywords
    keywords = [
        'and', 'as', 'assert',
        'break',
        'class', 'continue',
        'def', 'del',
        'elif', 'else', 'except',
        'finally', 'for', 'from',
        'global',
        'if', 'import', 'in', 'is',
        'lambda',
        'not',
        'or',
        'pass',
        'raise', 'return',
        'try',
        'while', 'with',
        'yield',

        '__debug__',

        'False',
        'None',
        'True',
        '\.\.\.',
    ]

    builtin = [
        'abs', 'all', 'any', 'ascii',
        'bin', 'bool', 'breakpoint', 'bytearray', 'bytes',
        'callable', 'chr', 'classmethod', 'compile', 'complex',
        'delattr', 'dict', 'dir', 'divmod',
        'enumerate', 'eval', 'exec', 'exit',
        'filter', 'float', 'format', 'frozenset',
        'getattr', 'globals',
        'hasattr', 'hash', 'help', 'hex',
        'id', 'input', 'int', 'isinstance', 'issubclass', 'iter',
        'len', 'list', 'locals',
        'map', 'max', 'memoryview', 'min',
        'next'
        'object', 'oct', 'open', 'ord',
        'pow', 'print', 'property',
        'range', 'repr', 'reversed', 'round',
        'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super',
        'tuple', 'type',
        'vars',
        'zip',
        '__import__',

        'Ellipsis'
        'NotImplemented'
    ]

    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '\+', '-', '\*', '/', '//', '\%', '\*\*', '@',
        # In-place
        '\+=', '-=', '\*=', '/=', '\%=',
        # Bitwise
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    # Python braces
    braces = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]

    def __init__(self, document, styles=...):
        QSyntaxHighlighter.__init__(self, document)
        if styles is ...:
            styles = STYLES

        # Multi-line strings (expression, flag, style)
        # syntax highlighting from this point onward
        self.tri_single = (QRegExp("'''"), 1, styles['string2'])
        self.tri_double = (QRegExp('"""'), 2, styles['string2'])

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, styles['keyword'])
                  for w in Python3Highlighter.keywords]
        rules += [(r'\b%s\b' % w, 0, styles['builtin'])
                  for w in Python3Highlighter.builtin]
        rules += [(r'%s' % o, 0, styles['operator'])
                  for o in Python3Highlighter.operators]
        rules += [(r'%s' % b, 0, styles['brace'])
                  for b in Python3Highlighter.braces]

        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, styles['self']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, styles['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, styles['string']),

            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, styles['defclass']),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, styles['defclass']),

            # From '#' until a newline
            (r'#[^\n]*', 0, styles['comment']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, styles['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, styles['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, styles['numbers']),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
                      for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        if not self.match_multiline(text, *self.tri_single):
            self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False
