
from decorator import decorator
import threading
import time
import urlparse

__all__ = ['metric',
           'MetricDecorator',
           'set_statsd_client',
           'statsd_client',
           'statsd_client_from_uri',
           'statsd_client_stack',
           ]


class _ClientStack(threading.local):
    """Thread local stack of statsd clients.

    Applications and tests can either set the global statsd client using
    set_statsd_client() or set a statsd client for each thread
    using statsd_client_stack.push()/.pop().

    This is like pyramid.threadlocal but it handles the default differently.
    """
    default = None

    def __init__(self):
        self.stack = []

    def push(self, obj):
        self.stack.append(obj)

    def pop(self):
        stack = self.stack
        if stack:
            return stack.pop()

    def get(self):
        stack = self.stack
        if stack:
            return stack[-1]
        else:
            return self.default

    def clear(self):
        del self.stack[:]


statsd_client_stack = _ClientStack()


def statsd_client():
    return statsd_client_stack.get()


def set_statsd_client(client_or_uri):
    if isinstance(client_or_uri, basestring):
        client = statsd_client_from_uri(client_or_uri)
    else:
        client = client_or_uri
    _ClientStack.default = client


def statsd_client_from_uri(uri):
    parts = urlparse.urlsplit(uri)
    if parts.scheme == 'statsd':
        from metrical.statsdclient import StatsdClient
        return StatsdClient(parts.hostname, parts.port)
    else:
        raise ValueError("URI scheme not supported: %s" % uri)


class MetricDecorator(object):

    def __init__(self, stats=None, sample_rate=1, method=False,
                 count=True, timing=True):
        if isinstance(stats, basestring):
            stats = [stats]

        self.stats = stats
        self.sample_rate = sample_rate
        self.method = method
        self.count = count
        self.timing = timing

    def __call__(self, f):
        """Decorate a function or method so it can send statistics to statsd.
        """
        instance_stats = self.stats
        sample_rate = self.sample_rate
        method = self.method
        count = self.count
        timing = self.timing

        def _call(func, *args, **kw):
            client = statsd_client_stack.get()
            if client is None:
                # No statsd client has been configured.
                return func(*args, **kw)

            if instance_stats:
                stats = instance_stats
            elif method:
                cls = args[0].__class__
                stats = ['%s.%s.%s' %
                         (cls.__module__, cls.__name__, func.__name__)]
            else:
                stats = ['%s.%s' % (func.__module__, func.__name__)]

            if count:
                client.update_stats(stats, 1, sample_rate)

            if timing:
                start = time.time()
                try:
                    return func(*args, **kw)
                finally:
                    elapsed_ms = int((time.time() - start) * 1000)
                    for stat in stats:
                        client.timing(stat, elapsed_ms, sample_rate)
            else:
                return func(*args, **kw)

        return decorator(_call, f)


# 'metric' is a function decorator with default options.
metric = MetricDecorator()

# 'metricmethod' is a method decorator with default options.
metricmethod = MetricDecorator(method=True)
