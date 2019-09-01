# cython: auto_pickle=False,embedsignature=True,always_allow_keywords=False
# -*- coding: utf-8 -*-
"""
Implementation of metrics.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import time
from types import MethodType
from weakref import WeakKeyDictionary
import functools
import random as stdrandom

from .clientstack import statsd_client
from .clientstack import client_stack as statsd_client_stack
from .statsd import StatsdClientMod
from .statsd import null_client

logger = __import__('logging').getLogger(__name__)

class _MethodLikeMixin(object):
    __slots__ = ()
    # We may be wrapped by another decorator,
    # so we can't count on __get__ being called.
    # But if it is, we need to act like a bound method.
    #
    # When we compile with Cython, we can't dynamically choose
    # a __get__ impl; the last one defined wins, so we must take the conditional
    # inside the method.
    def __get__(self, inst, klass):
        if inst is None:
            return self
        # Python 2 takes 3 arguments, Python 3 just two. Actually you
        # can get away with passing just the first two to Python 2,
        # but you get '<bound method ?.foo>' and possibly other issues
        # (im_class is None), so it's best to pass all three.
        return MethodType(self, inst, klass) if str is bytes else MethodType(self, inst)

class _AbstractMetricImpl(_MethodLikeMixin):
    __slots__ = (
        'f',
        'random',
        'metric_timing',
        'metric_count',
        'metric_rate',
        'timing_format',
        '__wrapped__',
        '__dict__',
    )
    stat_name = None
    def __init__(self, f, timing, count, rate, timing_format, random):
        self.__wrapped__ = None
        self.f = f
        self.metric_timing = timing
        self.metric_count = count
        self.metric_rate = rate
        self.timing_format = timing_format
        self.random = random

    def __call__(self, *args, **kwargs):
        if self.metric_rate < 1 and self.random() >= self.metric_rate:
            # Ignore this sample.
            return self.f(*args, **kwargs)

        client = statsd_client()

        if client is None:
            # No statsd client has been configured.
            return self.f(*args, **kwargs)

        stat = self.stat_name or self._compute_stat(args)
        # TODO: A lot of this is duplicated with __exit__.
        # Can we do better?
        if self.metric_timing:
            if self.metric_count:
                buf = []
                client.incr(stat, 1, self.metric_rate, buf=buf, rate_applied=True)
            else:
                buf = None

            start = time()

            try:
                return self.f(*args, **kwargs)
            finally:
                end = time()
                elapsed_ms = int((end - start) * 1000.0)
                client.timing(self.timing_format % stat, elapsed_ms,
                              self.metric_rate, buf=buf, rate_applied=True)
                if buf:
                    client.sendbuf(buf)

        else:
            if self.metric_count:
                client.incr(stat, 1, self.metric_rate, rate_applied=True)
            return self.f(*args, **kwargs)

    def _compute_stat(self, args):
        raise NotImplementedError

class _GivenStatMetricImpl(_AbstractMetricImpl):
    __slots__ = (
        'stat_name',
    )
    def __init__(self, stat_name, *args):
        self.stat_name = stat_name
        super(_GivenStatMetricImpl, self).__init__(*args)

    def _compute_stat(self, args): # pragma: no cover
        return self.stat_name

class _MethodMetricImpl(_AbstractMetricImpl):
    __slots__ = (
        'klass_dict',
    )

    def __init__(self, *args):
        self.klass_dict = WeakKeyDictionary()
        super(_MethodMetricImpl, self).__init__(*args)

    def _compute_stat(self, args):
        klass = args[0].__class__
        try:
            stat_name = self.klass_dict[klass]
        except KeyError:
            stat_name = '%s.%s.%s' % (klass.__module__, klass.__name__, self.f.__name__)
            self.klass_dict[klass] = stat_name
        return stat_name


class Metric(object):
    """
    Metric(stat=None, rate=1, method=False, count=True, timing=True)

    A decorator or context manager with options.

    ``stat`` is the name of the metric to send; set it to None to use
    the name of the function or method. ``rate`` lets you reduce the
    number of packets sent to Statsd by selecting a random sample; for
    example, set it to 0.1 to send one tenth of the packets. If the
    ``method`` parameter is true, the default metric name is based on
    the method's class name rather than the module name. Setting
    ``count`` to False disables the counter statistics sent to Statsd.
    Setting ``timing`` to False disables the timing statistics sent to
    Statsd.

    Sample use as a decorator::

        @Metric('frequent_func', rate=0.1, timing=False)
        def frequent_func():
            "Do something fast and frequently."

    Sample use as a context manager::

        def do_something():
            with Metric('doing_something'):
                pass

    If perfmetrics sends packets too frequently, UDP packets may be lost
    and the application performance may be affected.  You can reduce
    the number of packets and the CPU overhead using the ``Metric``
    decorator with options instead of `metric` or `metricmethod`.
    The decorator example above uses a sample rate and a static metric name.
    It also disables the collection of timing information.

    When using Metric as a context manager, you must provide the
    ``stat`` parameter or nothing will be recorded.

    .. versionchanged:: 3.0

        When used as a decorator, set ``__wrapped__`` on the returned object, even
        on Python 2.

    .. versionchanged:: 3.0

        When used as a decorator, the returned object
        has ``metric_timing``, ``metric_count`` and ``metric_rate``
        attributes that can be changed to alter its behaviour.

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
        self.start = 0.0

    def __call__(self, f):
        """
        Decorate a function or method so it can send statistics to statsd.
        """
        func_name = f.__name__
        func_full_name = '%s.%s' % (f.__module__, func_name)

        if self.method:
            metric = _MethodMetricImpl(f, self.timing, self.count,
                                       self.rate, self.timing_format,
                                       self.random)
        else:
            metric = _GivenStatMetricImpl(
                self.stat or func_full_name,
                f, self.timing, self.count,
                self.rate, self.timing_format,
                self.random)

        metric = functools.update_wrapper(metric, f)
        metric.__wrapped__ = f # Python 2 doesn't set this, but it's handy to have.
        return metric

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

        @functools.wraps(f)
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

        call_with_mod.__wrapped__ = f
        return call_with_mod

    def __enter__(self):
        client = statsd_client_stack.get()

        if client is None:
            statsd_client_stack.push(null_client)
        else:
            statsd_client_stack.push(StatsdClientMod(client, self.format))

    def __exit__(self, _typ, _value, _tb):
        statsd_client_stack.pop()

# pylint:disable=wrong-import-position,wrong-import-order
from perfmetrics._util import import_c_accel
import_c_accel(globals(), 'perfmetrics._metric')
