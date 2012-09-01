
"""perfmetrics is a library for sending software performance metrics to statsd.
"""

from perfmetrics.clientstack import ClientStack
from perfmetrics.clientstack import client_stack
from perfmetrics.statsd import StatsdClient
from time import time
import functools
import socket
import threading

try:  # pragma no cover
    # Python 3
    from urllib.parse import urlsplit
    from urllib.parse import parse_qsl
    from urllib.parse import uses_query

    basestring = str

except ImportError:  # pragma no cover
    # Python 2
    from urlparse import urlsplit
    from urlparse import parse_qsl
    from urlparse import uses_query


__all__ = ['metric',
           'Metric',
           'set_statsd_client',
           'statsd_client',
           'statsd_client_from_uri',
           'statsd_client_stack',
           ]


statsd_client_stack = client_stack


def statsd_client():
    """Return the current StatsdClient for the thread.

    Defaults to the global client set by ``set_statsd_client``.
    """
    return statsd_client_stack.get()


def set_statsd_client(client_or_uri):
    """Set the global StatsdClient.

    Accepts either a StatsdClient, a Statsd URI, or None (to clear the
    global client).
    """
    if isinstance(client_or_uri, basestring):
        client = statsd_client_from_uri(client_or_uri)
    else:
        client = client_or_uri
    ClientStack.default = client


if 'statsd' not in uses_query:
    uses_query.append('statsd')


def statsd_client_from_uri(uri):
    """Create and return StatsdClient.

    A typical URI is ``statsd://localhost:8125``.  An optional
    query parameter is ``gauge_suffix``.  The default gauge_suffix
    is ".<current_host_name>".
    """
    parts = urlsplit(uri)
    if parts.scheme == 'statsd':
        gauge_suffix = '.%s' % socket.gethostname()
        kw = {'gauge_suffix': gauge_suffix}
        if parts.query:
            kw.update(parse_qsl(parts.query))
        return StatsdClient(parts.hostname, parts.port, **kw)
    else:
        raise ValueError("URI scheme not supported: %s" % uri)


class Metric(object):
    """A factory of metric decorators."""

    def __init__(self, stat=None, sample_rate=1, method=False,
                 count=True, timing=True):
        self.stat = stat
        self.sample_rate = sample_rate
        self.method = method
        self.count = count
        self.timing = timing

    def __call__(self, f):
        """Decorate a function or method so it can send statistics to statsd.
        """
        func_name = f.__name__
        func_full_name = '%s.%s' % (f.__module__, func_name)

        instance_stat = self.stat
        sample_rate = self.sample_rate
        method = self.method
        count = self.count
        timing = self.timing

        def call_with_metric(*args, **kw):
            stack = statsd_client_stack.stack
            client = stack[-1] if stack else client_stack.default
            if client is None:
                # No statsd client has been configured.
                return f(*args, **kw)

            if instance_stat:
                stat = instance_stat
            elif method:
                cls = args[0].__class__
                stat = '%s.%s.%s' % (cls.__module__, cls.__name__, func_name)
            else:
                stat = func_full_name

            if timing:
                if count:
                    buf = []
                    client.change(stat, 1, sample_rate, buf=buf)
                else:
                    buf = None
                start = time()
                try:
                    return f(*args, **kw)
                finally:
                    elapsed_ms = int((time() - start) * 1000.0)
                    client.timing(stat, elapsed_ms, sample_rate, buf=buf)
                    if buf:
                        client.sendbuf(buf)

            else:
                if count:
                    client.change(stat, 1, sample_rate)
                return f(*args, **kw)

        return functools.update_wrapper(call_with_metric, f)


# 'metric' is a function decorator with default options.
metric = Metric()

# 'metricmethod' is a method decorator with default options.
metricmethod = Metric(method=True)
