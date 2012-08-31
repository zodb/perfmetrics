
import threading


class ClientStack(threading.local):
    """Thread local stack of StatsdClients.

    Applications and tests can either set the global statsd client using
    perfmetrics.set_statsd_client() or set a statsd client for each thread
    using statsd_client_stack.push()/.pop()/.clear().

    This is like pyramid.threadlocal but it handles the default differently.
    """

    default = None

    def __init__(self):
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
