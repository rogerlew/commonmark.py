from __future__ import unicode_literals

import re


reContainer = re.compile(
    r'(document|block_quote|list|item|paragraph|assertion|action|'
    r'heading|title|purpose|step|substep|meta|emph|strong|action_verb|point_state|link|image|'
    r'custom_inline|custom_block)')


def is_container(node):
    return (re.search(reContainer, node.t) is not None)


class NodeWalker(object):

    def __init__(self, root):
        self.current = root
        self.root = root
        self.entering = True

    def __next__(self):
        cur = self.current
        entering = self.entering

        if cur is None:
            raise StopIteration

        container = is_container(cur)

        if entering and container:
            if cur.first_child:
                self.current = cur.first_child
                self.entering = True
            else:
                # stay on node but exit
                self.entering = False
        elif cur == self.root:
            self.current = None
        elif cur.nxt is None:
            self.current = cur.parent
            self.entering = False
        else:
            self.current = cur.nxt
            self.entering = True

        return cur, entering

    next = __next__

    def __iter__(self):
        return self

    def nxt(self):
        """ for backwards compatibility """
        try:
            cur, entering = next(self)
            return {
                'entering': entering,
                'node': cur,
            }
        except StopIteration:
            return None

    def resume_at(self, node, entering):
        self.current = node
        self.entering = (entering is True)


class Node(object):
    def __init__(self, node_type, sourcepos):
        self.t = node_type
        self.parent = None
        self.first_child = None
        self.last_child = None
        self.prv = None
        self.nxt = None
        self.sourcepos = sourcepos
        self.last_line_blank = False
        self.last_line_checked = False
        self.is_open = True
        self.string_content = ''
        self.literal = None
        self.list_data = {}
        self.info = None
        self.destination = None
        self.title = None
        self.is_fenced = False
        self.fence_char = None
        self.fence_length = 0
        self.fence_offset = None
        self.level = None
        self.on_enter = None
        self.on_exit = None

    def __repr__(self):
        return "Node {} [{}]".format(self.t, self.literal)

    def pretty(self):
        from pprint import pprint
        pprint(self.__dict__)

    def normalize(self):
        prev = None
        for curr, _ in self.walker():
            if prev is None:
                prev = curr
                continue
            if prev.t == 'text' and curr.t == 'text':
                prev.literal += curr.literal
                curr.unlink()
            else:
                prev = curr

    def is_container(self):
        return is_container(self)

    def append_child(self, child):
        child.unlink()
        child.parent = self
        if self.last_child:
            self.last_child.nxt = child
            child.prv = self.last_child
            self.last_child = child
        else:
            self.first_child = child
            self.last_child = child

    def prepend_child(self, child):
        child.unlink()
        child.parent = self
        if self.first_child:
            self.first_child.prv = child
            child.nxt = self.first_child
            self.first_child = child
        else:
            self.first_child = child
            self.last_child = child

    def unlink(self):
        if self.prv:
            self.prv.nxt = self.nxt
        elif self.parent:
            self.parent.first_child = self.nxt

        if self.nxt:
            self.nxt.prv = self.prv
        elif self.parent:
            self.parent.last_child = self.prv

        self.parent = None
        self.nxt = None
        self.prv = None

    def insert_after(self, sibling):
        sibling.unlink()
        sibling.nxt = self.nxt
        if sibling.nxt:
            sibling.nxt.prv = sibling
        sibling.prv = self
        self.nxt = sibling
        sibling.parent = self.parent
        if not sibling.nxt:
            sibling.parent.last_child = sibling

    def insert_before(self, sibling):
        sibling.unlink()
        sibling.prv = self.prv
        if sibling.prv:
            sibling.prv.nxt = sibling
        sibling.nxt = self
        self.prv = sibling
        sibling.parent = self.parent
        if not sibling.prv:
            sibling.parent.first_child = sibling

    def walker(self):
        return NodeWalker(self)
