
from decorator import decorator
from metrical.clientstack import ClientStack
from metrical.clientstack import client_stack
import socket
import threading
import time
import urlparse

try:
    from metrical._cimpl import Metric
    from metrical._cimpl import StatsdClient
except ImportError:  # pragma: no cover
    from metrical._pyimpl import Metric
    from metrical._pyimpl import StatsdClient


__all__ = ['metric',
           'Metric',
           'set_statsd_client',
           'statsd_client',
           'statsd_client_from_uri',
           'statsd_client_stack',
           ]


statsd_client_stack = client_stack


def statsd_client():
    return statsd_client_stack.get()


def set_statsd_client(client_or_uri):
    if isinstance(client_or_uri, basestring):
        client = statsd_client_from_uri(client_or_uri)
    else:
        client = client_or_uri
    ClientStack.default = client


if 'statsd' not in urlparse.uses_query:
    urlparse.uses_query.append('statsd')


def statsd_client_from_uri(uri):
    """Create and return StatsdClient.

    >>> from metrical.statsdclient import statsd_client_from_uri
    >>> client = statsd_client_from_uri('statsd://localhost:8125')
    """
    parts = urlparse.urlsplit(uri)
    if parts.scheme == 'statsd':
        gauge_suffix = '.%s' % socket.gethostname()
        kw = {'gauge_suffix': gauge_suffix}
        if parts.query:
            kw.update(urlparse.parse_qsl(parts.query))
        return StatsdClient(parts.hostname, parts.port, **kw)
    else:
        raise ValueError("URI scheme not supported: %s" % uri)


# 'metric' is a function decorator with default options.
metric = Metric()

# 'metricmethod' is a method decorator with default options.
metricmethod = Metric(method=True)
