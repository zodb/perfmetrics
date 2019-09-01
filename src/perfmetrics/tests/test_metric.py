# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest

class MockStatsdClient(object):
    def __init__(self):
        self.changes = []
        self.timings = []
        self.sentbufs = []

    def incr(self, stat, count=1, rate=1, buf=None,
             rate_applied=False):
        self.changes.append((stat, count, rate, buf, rate_applied))
        if buf is not None:
            buf.append('count_line')

    def timing(self, stat, ms, rate, buf=None,
               rate_applied=False):
        self.timings.append((stat, ms, rate, buf, rate_applied))
        if buf is not None:
            buf.append('timing_line')

    def sendbuf(self, buf):
        self.sentbufs.append(buf)


class TestMetric(unittest.TestCase):

    def setUp(self):
        self.statsd_client_stack.clear()

    tearDown = setUp

    @property
    def _class(self):
        from perfmetrics import Metric
        return Metric

    def _makeOne(self, *args, **kwargs):
        return self._class(*args, **kwargs)

    @property
    def statsd_client_stack(self):
        from perfmetrics import statsd_client_stack
        return statsd_client_stack

    def _add_client(self):
        client = MockStatsdClient()
        self.statsd_client_stack.push(client)
        return client

    def test_ctor_with_defaults(self):
        obj = self._makeOne()
        self.assertIsNone(obj.stat)
        self.assertEqual(obj.rate, 1)
        self.assertTrue(obj.count)
        self.assertTrue(obj.timing)
        from perfmetrics import _util
        if not _util.PURE_PYTHON: # pragma: no cover
            self.assertIn('_metric', str(obj))
        else:
            self.assertNotIn('_metric', str(obj))

    def test_ctor_with_options(self):
        obj = self._makeOne('spam.n.eggs', 0.1, count=False, timing=False)
        self.assertEqual(obj.stat, 'spam.n.eggs')
        self.assertEqual(obj.rate, 0.1)
        self.assertFalse(obj.count)
        self.assertFalse(obj.timing)

    def test_decorate_function(self):
        args = []
        metric = self._makeOne()

        @metric
        def spam(x, y=2):
            args.append((x, y))

        self.assertEqual(spam.__module__, __name__)
        self.assertEqual(spam.__name__, 'spam')

        # Call with no statsd client configured.
        spam(4, 5)
        self.assertEqual(args, [(4, 5)])
        del args[:]

        # Call with a statsd client configured.
        client = self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])

        stat, delta, rate, buf, rate_applied = client.changes[0]
        self.assertEqual(stat, __name__ + '.spam')
        self.assertEqual(delta, 1)
        self.assertEqual(rate, 1)
        self.assertEqual(buf, ['count_line', 'timing_line'])
        self.assertTrue(rate_applied)

        self.assertEqual(len(client.timings), 1)
        stat, ms, rate, _buf, rate_applied = client.timings[0]
        self.assertEqual(stat, __name__ + '.spam.t')
        self.assertGreaterEqual(ms, 0)
        self.assertLess(ms, 10000)
        self.assertEqual(rate, 1)
        self.assertTrue(rate_applied)

        self.assertEqual(client.sentbufs, [['count_line', 'timing_line']])

    def test_decorate_method(self):
        args = []
        metricmethod = self._makeOne(method=True)

        class Spam(object):
            @metricmethod
            def f(self, x, y=2):
                args.append((self, x, y))

        self.assertEqual(Spam.f.__module__, __name__)
        self.assertEqual(Spam.f.__name__, 'f')

        # Call with no statsd client configured.
        spam = Spam()
        spam.f(4, 5)
        self.assertEqual(args, [(spam, 4, 5)])
        del args[:]

        # Call with a statsd client configured.
        client = self._add_client()
        spam.f(6, 1)
        self.assertEqual(args, [(spam, 6, 1)])

        self.assertEqual(len(client.changes), 1)
        __traceback_info__ = client.changes
        stat, delta, rate, buf, rate_applied = client.changes[0]
        self.assertEqual(stat, __name__ + '.Spam.f')
        self.assertEqual(delta, 1)
        self.assertEqual(rate, 1)
        self.assertEqual(buf, ['count_line', 'timing_line'])
        self.assertTrue(rate_applied)

        self.assertEqual(len(client.timings), 1)
        stat, ms, rate, _buf, rate_applied = client.timings[0]
        self.assertEqual(stat, __name__ + '.Spam.f.t')
        self.assertGreaterEqual(ms, 0)
        self.assertLess(ms, 10000)
        self.assertEqual(rate, 1)
        self.assertTrue(rate_applied)

        self.assertEqual(client.sentbufs, [['count_line', 'timing_line']])

    def test_decorate_can_change_timing(self):
        metric = self._makeOne()
        args = []
        @metric
        def spam(x, y=2):
            args.append((x, y))

        metric = spam.__wrapped__ if not hasattr(spam, 'metric_timing') else spam

        self.assertTrue(metric.metric_timing)
        self.assertTrue(metric.metric_count)
        self.assertEqual(1, metric.metric_rate)
        metric.metric_rate = 0
        metric.metric_timing = False
        metric.metric_count = False
        # Call with a statsd client configured.
        client = self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])

        self.assertEqual(len(client.changes), 0)

    def test_decorate_method_can_change_timing(self):
        metricmethod = self._makeOne(method=True)
        args = []
        class Spam(object):
            @metricmethod
            def f(self, x, y=2):
                args.append((self, x, y))

        metric = Spam.f
        if not hasattr(metric, 'metric_timing'):
            metric = Spam.f.__wrapped__ # pylint:disable=no-member
        self.assertTrue(metric.metric_timing)
        self.assertTrue(metric.metric_count)
        self.assertEqual(1, metric.metric_rate)
        metric.metric_rate = 0
        metric.metric_timing = False
        metric.metric_count = False
        # Call with a statsd client configured.
        client = self._add_client()
        spam = Spam()
        spam.f(6, 1)
        self.assertEqual(args, [(spam, 6, 1)])

        self.assertEqual(len(client.changes), 0)


    def test_decorate_without_timing(self):
        args = []
        Metric = self._makeOne

        @Metric('spammy', rate=0.01, timing=False, random=lambda: 0.001)
        def spam(x, y=2):
            args.append((x, y))

        self.assertEqual(spam.__module__, __name__)
        self.assertEqual(spam.__name__, 'spam')

        # Call with no statsd client configured.
        spam(4, 5)
        self.assertEqual(args, [(4, 5)])
        del args[:]

        # Call with a statsd client configured.
        client = self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])

        self.assertEqual(len(client.changes), 1)
        stat, delta, rate, buf, rate_applied = client.changes[0]
        self.assertEqual(stat, 'spammy')
        self.assertEqual(delta, 1)
        self.assertEqual(rate, 0.01)
        self.assertIsNone(buf)
        self.assertTrue(rate_applied)

        self.assertEqual(len(client.timings), 0)
        self.assertEqual(client.sentbufs, [])

    def test_decorate_without_count(self):
        args = []
        Metric = self._makeOne

        @Metric(count=False)
        def spam(x, y=2):
            args.append((x, y))

        self.assertEqual(spam.__module__, __name__)
        self.assertEqual(spam.__name__, 'spam')

        # Call with no statsd client configured.
        spam(4, 5)
        self.assertEqual(args, [(4, 5)])
        del args[:]

        # Call with a statsd client configured.
        client = self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])
        self.assertEqual(client.changes, [])
        self.assertEqual(len(client.timings), 1)

        stat, ms, rate, buf, rate_applied = client.timings[0]
        self.assertEqual(stat, __name__ + '.spam.t')
        self.assertGreaterEqual(ms, 0)
        self.assertLess(ms, 10000)
        self.assertEqual(rate, 1)
        self.assertIsNone(buf)
        self.assertTrue(rate_applied)

        self.assertEqual(client.sentbufs, [])

    def test_decorate_with_neither_timing_nor_count(self):
        args = []
        Metric = self._makeOne

        @Metric(count=False, timing=False)
        def spam(x, y=2):
            args.append((x, y))

        # Call with no statsd client configured.
        spam(4, 5)
        self.assertEqual(args, [(4, 5)])
        del args[:]

        # Call with a statsd client configured.
        client = self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])
        self.assertEqual(client.changes, [])
        self.assertEqual(len(client.timings), 0)

        self.assertEqual(client.sentbufs, [])

    def test_ignore_function_sample(self):
        args = []
        Metric = self._makeOne

        @Metric(rate=0.99, random=lambda: 0.999)
        def spam(x, y=2):
            args.append((x, y))
            return 77

        client = self._add_client()
        self.assertEqual(77, spam(6, 1))

        # The function was called
        self.assertEqual(args, [(6, 1)])

        # No packets were sent because the random value was too high.
        self.assertFalse(client.changes)
        self.assertFalse(client.timings)
        self.assertFalse(client.sentbufs)

    def test_as_context_manager_with_stat_name(self):
        args = []
        Metric = self._makeOne

        def spam(x, y=2):
            with Metric('thing-done'):
                args.append((x, y))

        # Call with no statsd client configured.
        spam(4, 5)
        self.assertEqual(args, [(4, 5)])
        del args[:]

        # Call with a statsd client configured.
        client = self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])

        stat, delta, rate, buf, rate_applied = client.changes[0]
        self.assertEqual(stat, 'thing-done')
        self.assertEqual(delta, 1)
        self.assertEqual(rate, 1)
        self.assertEqual(buf, ['count_line', 'timing_line'])
        self.assertTrue(rate_applied)

        self.assertEqual(len(client.timings), 1)
        stat, ms, rate, _buf, rate_applied = client.timings[0]
        self.assertEqual(stat, 'thing-done.t')
        self.assertGreaterEqual(ms, 0)
        self.assertLess(ms, 10000)
        self.assertEqual(rate, 1)
        self.assertTrue(rate_applied)

        self.assertEqual(client.sentbufs, [['count_line', 'timing_line']])

    def test_ignore_context_manager_sample(self):
        args = []
        Metric = self._makeOne

        def spam(x, y=2):
            with Metric('thing-done', rate=0.99, random=lambda: 0.999):
                args.append((x, y))
                return 88

        client = self._add_client()
        self.assertEqual(88, spam(6, 716))

        # The function was called
        self.assertEqual(args, [(6, 716)])

        # No packets were sent because the random value was too high.
        self.assertFalse(client.changes)
        self.assertFalse(client.timings)
        self.assertFalse(client.sentbufs)

    def test_as_context_manager_without_stat_name(self):
        args = []
        Metric = self._makeOne

        def spam(x, y=2):
            with Metric():
                args.append((x, y))

        client = self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])

        self.assertFalse(client.changes)
        self.assertFalse(client.timings)
        self.assertFalse(client.sentbufs)

    def test_as_context_manager_without_timing(self):
        args = []
        Metric = self._makeOne

        def spam(x, y=2):
            with Metric('thing-done', timing=False):
                args.append((x, y))

        client = self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])

        self.assertEqual(len(client.changes), 1)

        stat, delta, rate, buf, rate_applied = client.changes[0]
        self.assertEqual(stat, 'thing-done')
        self.assertEqual(delta, 1)
        self.assertEqual(rate, 1)
        self.assertEqual(buf, ['count_line'])
        self.assertTrue(rate_applied)

        self.assertEqual(len(client.timings), 0)

        self.assertEqual(client.sentbufs, [['count_line']])

    def test_as_context_manager_without_count(self):
        args = []
        Metric = self._makeOne

        def spam(x, y=2):
            with Metric('thing-done', count=False):
                args.append((x, y))

        # Call with a statsd client configured.
        client = self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])

        self.assertEqual(len(client.changes), 0)
        self.assertEqual(len(client.timings), 1)
        stat, ms, rate, _buf, rate_applied = client.timings[0]
        self.assertEqual(stat, 'thing-done.t')
        self.assertGreaterEqual(ms, 0)
        self.assertLess(ms, 10000)
        self.assertEqual(rate, 1)
        self.assertTrue(rate_applied)

        self.assertEqual(client.sentbufs, [['timing_line']])

    def test_as_context_manager_with_neither_count_nor_timing(self):
        args = []
        Metric = self._makeOne

        def spam(x, y=2):
            with Metric('thing-done', count=False, timing=False):
                args.append((x, y))

        # Call with a statsd client configured.
        client = self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])

        self.assertEqual(len(client.changes), 0)
        self.assertEqual(len(client.timings), 0)
        self.assertEqual(client.sentbufs, [])

class SequenceDecorator(object):

    def __init__(self, *args, **kwargs):
        from perfmetrics import Metric
        from perfmetrics import MetricMod

        self.args = args
        self.kwargs = kwargs
        self.metric = Metric(*args, **kwargs)
        self.metricmod = MetricMod("%s")

    def __getattr__(self, name):
        return getattr(self.metric, name)

    def __call__(self, func):
        return self.metricmod(self.metric(func))

    def __enter__(self):
        self.metricmod.__enter__()
        self.metric.__enter__()

    def __exit__(self, t, v, tb):
        self.metric.__exit__(t, v, tb)
        self.metricmod.__exit__(t, v, tb)

    def __str__(self):
        return str(self.metricmod)


class TestMetricMod(TestMetric):

    def _makeOne(self, *args, **kwargs):
        return SequenceDecorator(*args, **kwargs)
