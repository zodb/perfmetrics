# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import threading

from .statsd import statsd_client_from_uri

string_types = (str,)
if str is bytes: # pragma: no cover
    string_types += (unicode,) # pylint:disable=undefined-variable

class ClientStack(threading.local):
    """
    Thread local stack of StatsdClients.

    Applications and tests can either set the global statsd client using
    perfmetrics.set_statsd_client() or set a statsd client for each thread
    using statsd_client_stack.push()/.pop()/.clear().

    This is like pyramid.threadlocal but it handles the default differently.
    """

    default = None

    def __init__(self):
        threading.local.__init__(self)
        self.stack = []

    def get(self):
        stack = self.stack
        return stack[-1] if stack else self.default

    def push(self, obj):
        self.stack.append(obj)

    def pop(self):
        stack = self.stack
        if stack:
            return stack.pop()

    def clear(self):
        del self.stack[:]


client_stack = ClientStack()

def statsd_client():
    """Return the current StatsdClient for the thread.

    Defaults to the global client set by `set_statsd_client`.
    """
    return client_stack.get()


def set_statsd_client(client_or_uri):
    """Set the global StatsdClient.

    Accepts either a StatsdClient, a Statsd URI, or None (to clear the
    global client).
    """
    if isinstance(client_or_uri, string_types):
        client = statsd_client_from_uri(client_or_uri)
    else:
        client = client_or_uri
    ClientStack.default = client
