
"""perfmetrics is a library for sending software performance metrics to statsd.
"""

from perfmetrics.clientstack import ClientStack
from perfmetrics.clientstack import client_stack
from perfmetrics.statsd import StatsdClient
from perfmetrics.statsd import StatsdClientMod
from perfmetrics.statsd import null_client
from time import time
import functools
import os
import random
import six


try:  # pragma no cover
    # Python 3
    from urllib.parse import urlsplit
    from urllib.parse import parse_qsl
    from urllib.parse import uses_query

    basestring = str  # @ReservedAssignment

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


if 'statsd' not in uses_query:  # pragma: no cover
    uses_query.append('statsd')


def statsd_client_from_uri(uri):
    """Create and return StatsdClient.

    A typical URI is ``statsd://localhost:8125``.  An optional
    query parameter is ``prefix``. The default prefix is an empty string.
    """
    parts = urlsplit(uri)
    if parts.scheme == 'statsd':
        kw = {}
        if parts.query:
            kw.update(parse_qsl(parts.query))
        return StatsdClient(parts.hostname, parts.port, **kw)
    else:
        raise ValueError("URI scheme not supported: %s" % uri)


class Metric(object):
    """Make metric decorator/context managers.

    Examples:

    @Metric('some.func')
    def somefunc():
        ...


    @metric
    def somefunc():
        ...
    """

    def __init__(self, stat=None, rate=1, method=False,
                 count=True, timing=True, timing_format='%s.t',
                 random=random.random):  # testing hook
        self.stat = stat
        self.rate = rate
        self.method = method
        self.count = count
        self.timing = timing
        self.timing_format = timing_format
        self.random = random

    def __call__(self, f):
        """Decorate a function or method so it can send statistics to statsd.
        """
        func_name = f.__name__
        func_full_name = '%s.%s' % (f.__module__, func_name)

        instance_stat = self.stat
        rate = self.rate
        method = self.method
        count = self.count
        timing = self.timing
        timing_format = self.timing_format
        random = self.random

        def call_with_metric(*args, **kw):
            if rate < 1 and random() >= rate:
                # Ignore this sample.
                return f(*args, **kw)

            stack = statsd_client_stack.stack
            client = stack[-1] if stack else client_stack.default
            if client is None:
                # No statsd client has been configured.
                return f(*args, **kw)

            if instance_stat:
                stat = instance_stat
            elif method:
                if isinstance(args[0], (type, six.class_types)):
                    cls = args[0]
                else:
                    cls = args[0].__class__
                stat = '%s.%s.%s' % (cls.__module__, cls.__name__, func_name)
            else:
                stat = func_full_name

            if timing:
                if count:
                    buf = []
                    client.incr(stat, 1, rate, buf=buf, rate_applied=True)
                else:
                    buf = None
                start = time()
                try:
                    return f(*args, **kw)
                finally:
                    elapsed_ms = int((time() - start) * 1000.0)
                    client.timing(timing_format % stat, elapsed_ms,
                                  rate, buf=buf, rate_applied=True)
                    if buf:
                        client.sendbuf(buf)

            else:
                if count:
                    client.incr(stat, 1, rate, rate_applied=True)
                return f(*args, **kw)

        return functools.update_wrapper(call_with_metric, f)

    # Metric can also be used as a context manager.

    def __enter__(self):
        self.start = time()

    def __exit__(self, _typ, _value, _tb):
        rate = self.rate
        if rate < 1 and self.random() >= rate:
            # Ignore this sample.
            return

        stack = statsd_client_stack.stack
        client = stack[-1] if stack else client_stack.default
        if client is not None:
            buf = []
            stat = self.stat
            if stat:
                if self.count:
                    client.incr(stat, rate=rate, buf=buf, rate_applied=True)
                if self.timing:
                    elapsed = int((time() - self.start) * 1000.0)
                    client.timing(self.timing_format % stat, elapsed,
                                  rate=rate, buf=buf, rate_applied=True)
                if buf:
                    client.sendbuf(buf)


# 'metric' is a function decorator with default options.
metric = Metric()

# 'metricmethod' is a method decorator with default options.
metricmethod = Metric(method=True)


class MetricMod(object):
    """Decorator/context manager that modifies the name of metrics in context.

    format is a format string such as 'XYZ.%s'.
    """

    def __init__(self, format):
        self.format = format

    def __call__(self, f):
        """Decorate a function or method to add a metric prefix in context.
        """

        def call_with_mod(*args, **kw):
            stack = statsd_client_stack.stack
            client = stack[-1] if stack else client_stack.default
            if client is None:
                # Statsd is not configured.
                return f(*args, **kw)

            stack.append(StatsdClientMod(client, self.format))
            try:
                return f(*args, **kw)
            finally:
                stack.pop()

        return functools.update_wrapper(call_with_mod, f)

    def __enter__(self):
        stack = statsd_client_stack.stack
        client = stack[-1] if stack else client_stack.default
        if client is None:
            stack.append(null_client)
        else:
            stack.append(StatsdClientMod(client, self.format))

    def __exit__(self, _typ, _value, _tb):
        stack = statsd_client_stack.stack
        stack.pop()


_uri = os.environ.get('STATSD_URI')
if _uri:
    set_statsd_client(_uri)  # pragma no cover


#==============================================================================
# Optional Pyramid integration
#==============================================================================


def includeme(config):
    """Pyramid configuration hook: activate the perfmetrics tween.

    A statsd_uri should be in the settings.
    """
    if config.registry.settings.get('statsd_uri'):
        config.add_tween('perfmetrics.tween')


def tween(handler, registry):
    """Pyramid tween that sets up a Statsd client for each request.
    """
    uri = registry.settings['statsd_uri']
    client = statsd_client_from_uri(uri)

    def handle(request):
        statsd_client_stack.push(client)
        try:
            with Metric('perfmetrics.tween'):
                return handler(request)
        finally:
            statsd_client_stack.pop()

    return handle


#==============================================================================
# Optional WSGI integration
#==============================================================================


def make_statsd_app(nextapp, _globals=None, statsd_uri=''):
    """Create a WSGI filter app that sets up Statsd for each request."""
    if not statsd_uri:
        # Disabled.
        return nextapp

    client = statsd_client_from_uri(statsd_uri)

    def app(environ, start_response):
        statsd_client_stack.push(client)
        try:
            with Metric('perfmetrics.wsgi'):
                return nextapp(environ, start_response)
        finally:
            statsd_client_stack.pop()

    return app
