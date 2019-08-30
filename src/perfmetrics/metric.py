# -*- coding: utf-8 -*-
"""
Implementation of metrics.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import time
import functools
import random as stdrandom

from .clientstack import client_stack as statsd_client_stack
from .statsd import StatsdClientMod
from .statsd import null_client

logger = __import__('logging').getLogger(__name__)

class Metric(object):
    """
    Make metric decorator/context managers.

    Examples::

        @Metric('some.func')
        def somefunc():
            ...

        @metric
        def somefunc():
            ...
    """

    def __init__(self, stat=None, rate=1, method=False,
                 count=True, timing=True, timing_format='%s.t',
                 random=stdrandom.random):  # testing hook
        self.stat = stat
        self.rate = rate
        self.method = method
        self.count = count
        self.timing = timing
        self.timing_format = timing_format
        self.random = random
        self.start = None

    def __call__(self, f):
        """
        Decorate a function or method so it can send statistics to statsd.
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
        get_client = statsd_client_stack.get

        def call_with_metric(*args, **kw): # pylint:disable=too-many-branches
            if rate < 1 and random() >= rate:
                # Ignore this sample.
                return f(*args, **kw)

            client = get_client()

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

        client = statsd_client_stack.get()
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
            client = statsd_client_stack.get()
            if client is None:
                # Statsd is not configured.
                return f(*args, **kw)

            statsd_client_stack.push(StatsdClientMod(client, self.format))
            try:
                return f(*args, **kw)
            finally:
                statsd_client_stack.pop()

        return functools.update_wrapper(call_with_mod, f)

    def __enter__(self):
        client = statsd_client_stack.get()

        if client is None:
            statsd_client_stack.push(null_client)
        else:
            statsd_client_stack.push(StatsdClientMod(client, self.format))

    def __exit__(self, _typ, _value, _tb):
        statsd_client_stack.pop()
