from __future__ import absolute_import, unicode_literals, division

import re
import sys
from commonmark import common
from commonmark.common import normalize_uri, unescape_string
from commonmark.node import Node
from commonmark.normalize_reference import normalize_reference

if sys.version_info >= (3, 0):
    if sys.version_info >= (3, 4):
        import html
        HTMLunescape = html.unescape
    else:
        from .entitytrans import _unescape
        HTMLunescape = _unescape
else:
    from commonmark import entitytrans
    HTMLunescape = entitytrans._unescape

# Some regexps used in inline parser:

ESCAPED_CHAR = '\\\\' + common.ESCAPABLE

rePunctuation = re.compile(
    r'[!"#$%&\'()*+,\-./:;<=>?@\[\]\\^_`{|}~\xA1\xA7\xAB\xB6\xB7\xBB'
    r'\xBF\u037E\u0387\u055A-\u055F\u0589\u058A\u05BE\u05C0\u05C3'
    r'\u05C6\u05F3\u05F4\u0609\u060A\u060C\u060D\u061B\u061E\u061F'
    r'\u066A-\u066D\u06D4\u0700-\u070D\u07F7-\u07F9\u0830-\u083E'
    r'\u085E\u0964\u0965\u0970\u0AF0\u0DF4\u0E4F\u0E5A\u0E5B\u0F04-\u0F12'
    r'\u0F14\u0F3A-\u0F3D\u0F85\u0FD0-\u0FD4\u0FD9\u0FDA\u104A-\u104F\u10FB'
    r'\u1360-\u1368\u1400\u166D\u166E\u169B\u169C\u16EB-\u16ED\u1735\u1736'
    r'\u17D4-\u17D6\u17D8-\u17DA\u1800-\u180A\u1944\u1945\u1A1E\u1A1F\u1AA0-'
    r'\u1AA6\u1AA8-\u1AAD\u1B5A-\u1B60\u1BFC-\u1BFF\u1C3B-\u1C3F\u1C7E\u1C7F'
    r'\u1CC0-\u1CC7\u1CD3\u2010-\u2027\u2030-\u2043\u2045-\u2051\u2053-\u205E'
    r'\u207D\u207E\u208D\u208E\u2308-\u230B\u2329\u232A\u2768-\u2775\u27C5'
    r'\u27C6\u27E6-\u27EF\u2983-\u2998\u29D8-\u29DB\u29FC\u29FD\u2CF9-\u2CFC'
    r'\u2CFE\u2CFF\u2D70\u2E00-\u2E2E\u2E30-\u2E42\u3001-\u3003\u3008-\u3011'
    r'\u3014-\u301F\u3030\u303D\u30A0\u30FB\uA4FE\uA4FF\uA60D-\uA60F\uA673'
    r'\uA67E\uA6F2-\uA6F7\uA874-\uA877\uA8CE\uA8CF\uA8F8-\uA8FA\uA8FC\uA92E'
    r'\uA92F\uA95F\uA9C1-\uA9CD\uA9DE\uA9DF\uAA5C-\uAA5F\uAADE\uAADF\uAAF0'
    r'\uAAF1\uABEB\uFD3E\uFD3F\uFE10-\uFE19\uFE30-\uFE52\uFE54-\uFE61\uFE63'
    r'\uFE68\uFE6A\uFE6B\uFF01-\uFF03\uFF05-\uFF0A\uFF0C-\uFF0F\uFF1A\uFF1B'
    r'\uFF1F\uFF20\uFF3B-\uFF3D\uFF3F\uFF5B\uFF5D\uFF5F-\uFF65]|\uD800[\uDD00-'
    r'\uDD02\uDF9F\uDFD0]|\uD801\uDD6F|\uD802[\uDC57\uDD1F\uDD3F\uDE50-\uDE58'
    r'\uDE7F\uDEF0-\uDEF6\uDF39-\uDF3F\uDF99-\uDF9C]|\uD804[\uDC47-\uDC4D'
    r'\uDCBB\uDCBC\uDCBE-\uDCC1\uDD40-\uDD43\uDD74\uDD75\uDDC5-\uDDC9\uDDCD'
    r'\uDDDB\uDDDD-\uDDDF\uDE38-\uDE3D\uDEA9]|\uD805[\uDCC6\uDDC1-\uDDD7'
    r'\uDE41-\uDE43\uDF3C-\uDF3E]|\uD809[\uDC70-\uDC74]|\uD81A[\uDE6E\uDE6F'
    r'\uDEF5\uDF37-\uDF3B\uDF44]|\uD82F\uDC9F|\uD836[\uDE87-\uDE8B]'
)

reLinkTitle = re.compile(
    '^(?:"(' + ESCAPED_CHAR + '|[^"\\x00])*"' +
    '|' +
    '\'(' + ESCAPED_CHAR + '|[^\'\\x00])*\'' +
    '|' +
    '\\((' + ESCAPED_CHAR + '|[^()\\x00])*\\))')
reLinkDestinationBraces = re.compile(r'^(?:<(?:[^<>\n\\\x00]|\\.)*>)')

reEscapable = re.compile('^' + common.ESCAPABLE)
reEntityHere = re.compile('^' + common.ENTITY, re.IGNORECASE)
reTicks = re.compile(r'`+')
reTicksHere = re.compile(r'^`+')
reEllipses = re.compile(r'\.\.\.')
reDash = re.compile(r'--+')
reEmailAutolink = re.compile(
    r"^<([a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)>")
reAutolink = re.compile(
    r'^<[A-Za-z][A-Za-z0-9.+-]{1,31}:[^<>\x00-\x20]*>',
    re.IGNORECASE)
reSpnl = re.compile(r'^ *(?:\n *)?')
reWhitespaceChar = re.compile(r'^^[ \t\n\x0b\x0c\x0d]')
reWhitespace = re.compile(r'[ \t\n\x0b\x0c\x0d]+')
reUnicodeWhitespaceChar = re.compile(r'^\s')
reFinalSpace = re.compile(r' *$')
reInitialSpace = re.compile(r'^ *')
reSpaceAtEndOfLine = re.compile(r'^ *(?:\n|$)')
reLinkLabel = re.compile(r'^\[(?:[^\\\[\]]|\\.){0,1000}\]')
# Matches a string of non-special characters.
reMain = re.compile(r'^[^\n`\[\]\\!<&*_\'"]+', re.MULTILINE)


def text(s):
    node = Node('text', None)
    node.literal = s
    return node


def smart_dashes(chars):
    en_count = 0
    em_count = 0
    if len(chars) % 3 == 0:
        # If divisible by 3, use all em dashes
        em_count = len(chars) // 3
    elif len(chars) % 2 == 0:
        # If divisble by 2, use all en dashes
        en_count = len(chars) // 2
    elif len(chars) % 3 == 2:
        # if 2 extra dashes, use en dashfor last 2;
        # em dashes for rest
        en_count = 1
        em_count = (len(chars) - 2) // 3
    else:
        # Use en dashes for last 4 hyphens; em dashes for rest
        en_count = 2
        em_count = (len(chars) - 4) // 3
    return ('\u2014' * em_count) + ('\u2013' * en_count)


class InlineParser(object):
    """INLINE PARSER

    These are methods of an InlineParser class, defined below.
    An InlineParser keeps track of a subject (a string to be
    parsed) and a position in that subject.
    """

    def __init__(self, options={}):
        self.subject = ''
        self.brackets = None
        self.pos = 0
        self.refmap = {}
        self.options = options

    def match(self, regexString):
        """
        If regexString matches at current position in the subject, advance
        position in subject and return the match; otherwise return None.
        """
        match = re.search(regexString, self.subject[self.pos:])
        if match is None:
            return None
        else:
            self.pos += match.end()
            return match.group()

    def peek(self):
        """ Returns the character at the current subject position, or None if
        there are no more characters."""
        if self.pos < len(self.subject):
            return self.subject[self.pos]
        else:
            return None

    def spnl(self):
        """ Parse zero or more space characters, including at
        most one newline."""
        self.match(reSpnl)
        return True

    # All of the parsers below try to match something at the current position
    # in the subject.  If they succeed in matching anything, they
    # push an inline matched, advancing the subject.

    def parseBackticks(self, block):
        """ Attempt to parse backticks, adding either a backtick code span or a
        literal sequence of backticks to the 'inlines' list."""
        ticks = self.match(reTicksHere)
        if ticks is None:
            return False
        after_open_ticks = self.pos
        matched = self.match(reTicks)
        while matched is not None:
            if matched == ticks:
                node = Node('code', None)
                contents = self.subject[after_open_ticks:self.pos-len(ticks)] \
                    .replace('\n', ' ')
                if contents.lstrip(' ') and contents[0] == contents[-1] == ' ':
                    node.literal = contents[1:-1]
                else:
                    node.literal = contents
                block.append_child(node)
                return True
            matched = self.match(reTicks)
        # If we got here, we didn't match a closing backtick sequence.
        self.pos = after_open_ticks
        block.append_child(text(ticks))
        return True

    def parseBackslash(self, block):
        """
        Parse a backslash-escaped special character, adding either the
        escaped character, a hard line break (if the backslash is followed
        by a newline), or a literal backslash to the block's children.
        Assumes current character is a backslash.
        """
        subj = self.subject
        self.pos += 1

        try:
            subjchar = subj[self.pos]
        except IndexError:
            subjchar = None

        if self.peek() == '\n':
            self.pos += 1
            node = Node('linebreak', None)
            block.append_child(node)
        elif subjchar and re.search(reEscapable, subjchar):
            block.append_child(text(subjchar))
            self.pos += 1
        else:
            block.append_child(text('\\'))

        return True

    def parseAutolink(self, block):
        """Attempt to parse an autolink (URL or email in pointy brackets)."""
        m = self.match(reEmailAutolink)

        if m:
            # email
            dest = m[1:-1]
            node = Node('link', None)
            node.destination = normalize_uri('mailto:' + dest)
            node.title = ''
            node.append_child(text(dest))
            block.append_child(node)
            return True
        else:
            m = self.match(reAutolink)
            if m:
                # link
                dest = m[1:-1]
                node = Node('link', None)
                node.destination = normalize_uri(dest)
                node.title = ''
                node.append_child(text(dest))
                block.append_child(node)
                return True

        return False

    def parseHtmlTag(self, block):
        """Attempt to parse a raw HTML tag."""
        m = self.match(common.reHtmlTag)
        if m is None:
            return False
        else:
            node = Node('html_inline', None)
            node.literal = m
            block.append_child(node)
            return True

    def scanDelims(self, c):
        """
        Scan a sequence of characters == c, and return information about
        the number of delimiters and whether they are positioned such that
        they can open and/or close emphasis or strong emphasis.  A utility
        function for strong/emph parsing.
        """
        numdelims = 0
        startpos = self.pos

        if c == "'" or c == '"':
            numdelims += 1
            self.pos += 1
        else:
            while (self.peek() == c):
                numdelims += 1
                self.pos += 1

        if numdelims == 0:
            return None

        c_before = '\n' if startpos == 0 else self.subject[startpos - 1]

        c_after = self.peek()
        if c_after is None:
            c_after = '\n'

        # Python 2 doesn't recognize '\xa0' as whitespace
        after_is_whitespace = re.search(reUnicodeWhitespaceChar, c_after) or \
            c_after == '\xa0'
        after_is_punctuation = re.search(rePunctuation, c_after)
        before_is_whitespace = re.search(
            reUnicodeWhitespaceChar, c_before) or \
            c_before == '\xa0'
        before_is_punctuation = re.search(rePunctuation, c_before)

        left_flanking = not after_is_whitespace and \
            (not after_is_punctuation or
             before_is_whitespace or
             before_is_punctuation)
        right_flanking = not before_is_whitespace and \
            (not before_is_punctuation or
             after_is_whitespace or
             after_is_punctuation)
        if c == '_':
            can_open = left_flanking and \
                (not right_flanking or before_is_punctuation)
            can_close = right_flanking and \
                (not left_flanking or after_is_punctuation)
        elif c == "'" or c == '"':
            can_open = left_flanking and not right_flanking
            can_close = right_flanking
        else:
            can_open = left_flanking
            can_close = right_flanking

        self.pos = startpos
        return {
            'numdelims': numdelims,
            'can_open': can_open,
            'can_close': can_close,
        }

    def handleDelim(self, cc, block):
        """Handle a delimiter marker for emphasis or a quote."""
        res = self.scanDelims(cc)
        if not res:
            return False
        numdelims = res.get('numdelims')
        startpos = self.pos

        self.pos += numdelims
        if cc == "'":
            contents = '\u2019'
        elif cc == '"':
            contents = '\u201C'
        else:
            contents = self.subject[startpos:self.pos]
        node = text(contents)
        block.append_child(node)

        # Add entry to stack for this opener
        self.delimiters = {
            'cc': cc,
            'numdelims': numdelims,
            'origdelims': numdelims,
            'node': node,
            'previous': self.delimiters,
            'next': None,
            'can_open': res.get('can_open'),
            'can_close': res.get('can_close'),
        }
        if self.delimiters['previous'] is not None:
            self.delimiters['previous']['next'] = self.delimiters
        return True

    def removeDelimiter(self, delim):
        if delim.get('previous') is not None:
            delim['previous']['next'] = delim.get('next')
        if delim.get('next') is None:
            # Top of stack
            self.delimiters = delim.get('previous')
        else:
            delim['next']['previous'] = delim.get('previous')

    @staticmethod
    def removeDelimitersBetween(bottom, top):
        if bottom.get('next') != top:
            bottom['next'] = top
            top['previous'] = bottom

    def processEmphasis(self, stack_bottom):
        openers_bottom = {
            '_': stack_bottom,
            '*': stack_bottom,
            "'": stack_bottom,
            '"': stack_bottom,
        }
        odd_match = False
        use_delims = 0

        # Find first closer above stack_bottom
        closer = self.delimiters
        while closer is not None and closer.get('previous') != stack_bottom:
            closer = closer.get('previous')

        # Move forward, looking for closers, and handling each
        while closer is not None:
            if not closer.get('can_close'):
                closer = closer.get('next')
            else:
                # found emphasis closer. now look back for first
                # matching opener:
                opener = closer.get('previous')
                opener_found = False
                closercc = closer.get('cc')
                while (opener is not None and opener != stack_bottom and
                       opener != openers_bottom[closercc]):
                    odd_match = (closer.get('can_open') or
                                 opener.get('can_close')) and \
                                 closer['origdelims'] % 3 != 0 and \
                                 (opener['origdelims'] +
                                  closer['origdelims']) % 3 == 0
                    if opener.get('cc') == closercc and \
                       opener.get('can_open') and \
                       not odd_match:
                        opener_found = True
                        break
                    opener = opener.get('previous')
                old_closer = closer

                if closercc == '*' or closercc == '_':
                    if not opener_found:
                        closer = closer.get('next')
                    else:
                        # Calculate actual number of delimiters used from
                        # closer
                        use_delims = 2 if (
                            closer['numdelims'] >= 2 and
                            opener['numdelims'] >= 2) else 1

                        opener_inl = opener.get('node')
                        closer_inl = closer.get('node')

                        # Remove used delimiters from stack elts and inlines
                        opener['numdelims'] -= use_delims
                        closer['numdelims'] -= use_delims
                        opener_inl.literal = opener_inl.literal[
                            :len(opener_inl.literal) - use_delims]
                        closer_inl.literal = closer_inl.literal[
                            :len(closer_inl.literal) - use_delims]

                        # Build contents for new Emph element
                        if use_delims == 1:
                            emph = Node('emph', None)
                        else:
                            emph = Node(('point_state', 'action_verb')[closercc == '*'], None)

                        tmp = opener_inl.nxt
                        while tmp and tmp != closer_inl:
                            nxt = tmp.nxt
                            tmp.unlink()
                            emph.append_child(tmp)
                            tmp = nxt

                        opener_inl.insert_after(emph)

                        # Remove elts between opener and closer in delimiters
                        # stack
                        self.removeDelimitersBetween(opener, closer)

                        # If opener has 0 delims, remove it and the inline
                        if opener['numdelims'] == 0:
                            opener_inl.unlink()
                            self.removeDelimiter(opener)

                        if closer['numdelims'] == 0:
                            closer_inl.unlink()
                            tempstack = closer['next']
                            self.removeDelimiter(closer)
                            closer = tempstack

                elif closercc == "'":
                    closer['node'].literal = '\u2019'
                    if opener_found:
                        opener['node'].literal = '\u2018'
                    closer = closer['next']

                elif closercc == '"':
                    closer['node'].literal = '\u201D'
                    if opener_found:
                        opener['node'].literal = '\u201C'
                    closer = closer['next']

                if not opener_found and not odd_match:
                    # Set lower bound for future searches for openers:
                    # We don't do this with odd_match because a **
                    # that doesn't match an earlier * might turn into
                    # an opener, and the * might be matched by something
                    # else.
                    openers_bottom[closercc] = old_closer['previous']
                    if not old_closer['can_open']:
                        # We can remove a closer that can't be an opener,
                        # once we've seen there's no matching opener:
                        self.removeDelimiter(old_closer)

        # Remove all delimiters
        while self.delimiters is not None and self.delimiters != stack_bottom:
            self.removeDelimiter(self.delimiters)

    def parseLinkTitle(self):
        """
        Attempt to parse link title (sans quotes), returning the string
        or None if no match.
        """
        title = self.match(reLinkTitle)
        if title is None:
            return None
        else:
            # chop off quotes from title and unescape:
            return unescape_string(title[1:-1])

    def parseLinkDestination(self):
        """
        Attempt to parse link destination, returning the string or
        None if no match.
        """
        res = self.match(reLinkDestinationBraces)
        if res is None:
            if self.peek() == '<':
                return None
            # TODO handrolled parser; res should be None or the string
            savepos = self.pos
            openparens = 0
            while True:
                c = self.peek()
                if c is None:
                    break
                if c == '\\' and re.search(
                        reEscapable, self.subject[self.pos+1:self.pos+2]):
                    self.pos += 1
                    if self.peek() is not None:
                        self.pos += 1
                elif c == '(':
                    self.pos += 1
                    openparens += 1
                elif c == ')':
                    if openparens < 1:
                        break
                    else:
                        self.pos += 1
                        openparens -= 1
                elif re.search(reWhitespaceChar, c):
                    break
                else:
                    self.pos += 1
            if self.pos == savepos and c != ')':
                return None
            res = self.subject[savepos:self.pos]
            return normalize_uri(unescape_string(res))
        else:
            # chop off surrounding <..>:
            return normalize_uri(unescape_string(res[1:-1]))

    def parseLinkLabel(self):
        """
        Attempt to parse a link label, returning number of
        characters parsed.
        """
        # Note: our regex will allow something of form [..\];
        # we disallow it here rather than using lookahead in the regex:
        m = self.match(reLinkLabel)
        if m is None or len(m) > 1001:
            return 0
        else:
            return len(m)

    def parseOpenBracket(self, block):
        """
        Add open bracket to delimiter stack and add a text node to
        block's children.
        """
        startpos = self.pos
        self.pos += 1

        node = text('[')
        block.append_child(node)

        # Add entry to stack for this opener
        self.addBracket(node, startpos, False)
        return True

    def parseBang(self, block):
        """
        If next character is [, and ! delimiter to delimiter stack and
        add a text node to block's children. Otherwise just add a text
        node.
        """
        startpos = self.pos
        self.pos += 1
        if self.peek() == '[':
            self.pos += 1

            node = text('![')
            block.append_child(node)

            # Add entry to stack for this openeer
            self.addBracket(node, startpos + 1, True)
        else:
            block.append_child(text('!'))

        return True

    def parseCloseBracket(self, block):
        """
        Try to match close bracket against an opening in the delimiter
        stack. Add either a link or image, or a plain [ character,
        to block's children. If there is a matching delimiter,
        remove it from the delimiter stack.
        """
        title = None
        matched = False
        self.pos += 1
        startpos = self.pos

        # get last [ or ![
        opener = self.brackets

        if opener is None:
            # no matched opener, just return a literal
            block.append_child(text(']'))
            return True

        if not opener.get('active'):
            # no matched opener, just return a literal
            block.append_child(text(']'))
            # take opener off brackets stack
            self.removeBracket()
            return True

        # If we got here, opener is a potential opener
        is_image = opener.get('image')

        # Check to see if we have a link/image

        savepos = self.pos

        # Inline link?
        if self.peek() == '(':
            self.pos += 1
            self.spnl()
            dest = self.parseLinkDestination()
            if dest is not None and self.spnl():
                # make sure there's a space before the title
                if re.search(reWhitespaceChar, self.subject[self.pos-1]):
                    title = self.parseLinkTitle()
                if self.spnl() and self.peek() == ')':
                    self.pos += 1
                    matched = True
            else:
                self.pos = savepos

        if not matched:
            # Next, see if there's a link label
            beforelabel = self.pos
            n = self.parseLinkLabel()
            if n > 2:
                reflabel = self.subject[beforelabel:beforelabel + n]
            elif not opener.get('bracket_after'):
                # Empty or missing second label means to use the first
                # label as the reference.  The reference must not
                # contain a bracket. If we know there's a bracket, we
                # don't even bother checking it.
                reflabel = self.subject[opener.get('index'):startpos]
            if n == 0:
                # If shortcut reference link, rewind before spaces we skipped.
                self.pos = savepos

            if reflabel:
                # lookup rawlabel in refmap
                link = self.refmap.get(normalize_reference(reflabel))
                if link:
                    dest = link['destination']
                    title = link['title']
                    matched = True

        if matched:
            node = Node('image' if is_image else 'link', None)

            node.destination = dest
            node.title = title or ''
            tmp = opener.get('node').nxt
            while tmp:
                nxt = tmp.nxt
                tmp.unlink()
                node.append_child(tmp)
                tmp = nxt
            block.append_child(node)
            self.processEmphasis(opener.get('previousDelimiter'))
            self.removeBracket()
            opener.get('node').unlink()

            # We remove this bracket and processEmphasis will remove
            # later delimiters.
            # Now, for a link, we also deactivate earlier link openers.
            # (no links in links)
            if not is_image:
                opener = self.brackets
                while opener is not None:
                    if not opener.get('image'):
                        # deactivate this opener
                        opener['active'] = False
                    opener = opener.get('previous')

            return True
        else:
            # no match
            # remove this opener from stack
            self.removeBracket()
            self.pos = startpos
            block.append_child(text(']'))
            return True

    def addBracket(self, node, index, image):
        if self.brackets is not None:
            self.brackets['bracketAfter'] = True

        self.brackets = {
            'node': node,
            'previous': self.brackets,
            'previousDelimiter': self.delimiters,
            'index': index,
            'image': image,
            'active': True,
        }

    def removeBracket(self):
        self.brackets = self.brackets.get('previous')

    def parseEntity(self, block):
        """Attempt to parse an entity."""
        m = self.match(reEntityHere)
        if m:
            block.append_child(text(HTMLunescape(m)))
            return True
        else:
            return False

    def parseString(self, block):
        """
        Parse a run of ordinary characters, or a single character with
        a special meaning in markdown, as a plain string.
        """
        m = self.match(reMain)
        if m:
            if self.options.get('smart'):
                s = re.sub(reEllipses, '\u2026', m)
                s = re.sub(reDash, lambda x: smart_dashes(x.group()), s)
                block.append_child(text(s))
            else:
                block.append_child(text(m))
            return True
        else:
            return False

    def parseNewline(self, block):
        """
        Parse a newline.  If it was preceded by two spaces, return a hard
        line break; otherwise a soft line break.
        """
        # assume we're at a \n
        self.pos += 1
        lastc = block.last_child
        if lastc and lastc.t == 'text' and lastc.literal[-1] == ' ':
            linebreak = len(lastc.literal) >= 2 and lastc.literal[-2] == ' '
            lastc.literal = re.sub(reFinalSpace, '', lastc.literal)
            if linebreak:
                node = Node('linebreak', None)
            else:
                node = Node('softbreak', None)
            block.append_child(node)
        else:
            block.append_child(Node('softbreak', None))

        # gobble leading spaces in next line
        self.match(reInitialSpace)
        return True

    def parseReference(self, s, refmap):
        """Attempt to parse a link reference, modifying refmap."""
        self.subject = s
        self.pos = 0
        startpos = self.pos

        # label:
        match_chars = self.parseLinkLabel()
        if match_chars == 0 or match_chars == 2:
            return 0
        else:
            rawlabel = self.subject[:match_chars]

        # colon:
        if (self.peek() == ':'):
            self.pos += 1
        else:
            self.pos = startpos
            return 0

        # link url
        self.spnl()

        dest = self.parseLinkDestination()
        if dest is None:
            self.pos = startpos
            return 0

        beforetitle = self.pos
        self.spnl()
        title = None
        if self.pos != beforetitle:
            title = self.parseLinkTitle()
        if title is None:
            title = ''
            # rewind before spaces
            self.pos = beforetitle

        # make sure we're at line end:
        at_line_end = True
        if self.match(reSpaceAtEndOfLine) is None:
            if title == '':
                at_line_end = False
            else:
                # the potential title we found is not at the line end,
                # but it could still be a legal link reference if we
                # discard the title
                title == ''
                # rewind before spaces
                self.pos = beforetitle
                # and instead check if the link URL is at the line end
                at_line_end = self.match(reSpaceAtEndOfLine) is not None

        if not at_line_end:
            self.pos = startpos
            return 0

        normlabel = normalize_reference(rawlabel)
        if normlabel == '':
            # label must contain non-whitespace characters
            self.pos = startpos
            return 0

        if not refmap.get(normlabel):
            refmap[normlabel] = {
                'destination': dest,
                'title': title
            }
        return (self.pos - startpos)

    def parseInline(self, block):
        """
        Parse the next inline element in subject, advancing subject
        position.

        On success, add the result to block's children and return True.
        On failure, return False.
        """
        res = False
        c = self.peek()
        if c is None:
            return False
        if c == '\n':
            res = self.parseNewline(block)
        elif c == '\\':
            res = self.parseBackslash(block)
        elif c == '`':
            res = self.parseBackticks(block)
        elif c == '*' or c == '_':
            res = self.handleDelim(c, block)
        elif c == "'" or c == '"':
            res = self.options.get('smart') and self.handleDelim(c, block)
        elif c == '[':
            res = self.parseOpenBracket(block)
        elif c == '!':
            res = self.parseBang(block)
        elif c == ']':
            res = self.parseCloseBracket(block)
        elif c == '<':
            res = self.parseAutolink(block) or self.parseHtmlTag(block)
        elif c == '&':
            res = self.parseEntity(block)
        else:
            res = self.parseString(block)

        if not res:
            self.pos += 1
            block.append_child(text(c))

        return True

    def parseInlines(self, block):
        """
        Parse string content in block into inline children,
        using refmap to resolve references.
        """
        self.subject = block.string_content.strip()
        self.pos = 0
        self.delimiters = None
        self.brackets = None
        while (self.parseInline(block)):
            pass
        self.processEmphasis(None)

    parse = parseInlines
