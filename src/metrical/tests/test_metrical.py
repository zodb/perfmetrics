
try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestClientStack(unittest.TestCase):
    @property
    def _class(self):
        from metrical import _ClientStack
        return _ClientStack

    def test_ctor(self):
        obj = self._class()
        self.assertIsNotNone(obj.stack)

    def test_push(self):
        obj = self._class()
        client = object()
        obj.push(client)
        self.assertEqual(obj.stack, [client])

    def test_pop_with_client(self):
        obj = self._class()
        client = object()
        obj.stack.append(client)
        got = obj.pop()
        self.assertIs(got, client)
        self.assertEqual(obj.stack, [])

    def test_pop_without_client(self):
        obj = self._class()
        got = obj.pop()
        self.assertIsNone(got)
        self.assertEqual(obj.stack, [])

    def test_get_without_client(self):
        obj = self._class()
        self.assertIsNone(obj.get())

    def test_get_with_client(self):
        obj = self._class()
        client = object()
        obj.stack.append(client)
        self.assertIs(obj.get(), client)

    def test_clear(self):
        obj = self._class()
        client = object()
        obj.stack.append(client)
        obj.clear()
        self.assertEqual(obj.stack, [])


class Test_statsd_config_functions(unittest.TestCase):

    def setUp(self):
        from metrical import set_statsd_client
        set_statsd_client(None)

    tearDown = setUp

    def test_unconfigured(self):
        from metrical import statsd_client
        self.assertIsNone(statsd_client())

    def test_configured_with_uri(self):
        from metrical import set_statsd_client
        set_statsd_client('statsd://localhost:8125')
        from metrical.statsdclient import StatsdClient
        from metrical import statsd_client
        self.assertIsInstance(statsd_client(), StatsdClient)

    def test_configured_with_other_client(self):
        other_client = object()
        from metrical import set_statsd_client
        set_statsd_client(other_client)
        from metrical import statsd_client
        self.assertIs(statsd_client(), other_client)

    def test_unsupported_uri(self):
        from metrical import statsd_client_from_uri
        with self.assertRaises(ValueError):
            statsd_client_from_uri('http://localhost:8125')


class TestMetricDecorator(unittest.TestCase):

    def setUp(self):
        from metrical import statsd_client_stack
        statsd_client_stack.clear()

    tearDown = setUp

    def _add_client(self):
        self.updates = updates = []
        self.timing = timing = []

        class DummyStatsdClient:
            def update_stats(self, stats, delta, sample_rate):
                updates.append((stats, delta, sample_rate))

            def timing(self, stat, ms, sample_rate):
                timing.append((stat, ms, sample_rate))

        from metrical import statsd_client_stack
        statsd_client_stack.push(DummyStatsdClient())

    @property
    def _class(self):
        from metrical import MetricDecorator
        return MetricDecorator

    def test_ctor_with_defaults(self):
        obj = self._class()
        self.assertIsNone(obj.stats)
        self.assertEqual(obj.sample_rate, 1)
        self.assertTrue(obj.count)
        self.assertTrue(obj.timing)

    def test_ctor_with_options(self):
        obj = self._class('spam.n.eggs', 0.1, count=False, timing=False)
        self.assertEqual(obj.stats, ['spam.n.eggs'])
        self.assertEqual(obj.sample_rate, 0.1)
        self.assertFalse(obj.count)
        self.assertFalse(obj.timing)

    def test_ctor_with_multiple_stats(self):
        obj = self._class(['spam', 'eggs'])
        self.assertEqual(obj.stats, ['spam', 'eggs'])
        self.assertEqual(obj.sample_rate, 1)
        self.assertTrue(obj.count)
        self.assertTrue(obj.timing)

    def test_decorate_function(self):
        args = []

        from metrical import metric

        @metric
        def spam(x, y=2):
            args.append((x, y))

        self.assertEqual(spam.__module__, 'metrical.tests.test_metrical')
        self.assertEqual(spam.__name__, 'spam')

        # Call with no statsd client configured.
        spam(4, 5)
        self.assertEqual(args, [(4, 5)])
        del args[:]

        # Call with a statsd client configured.
        self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])
        self.assertEqual(self.updates,
                         [(['metrical.tests.test_metrical.spam'], 1, 1)])
        self.assertEqual(len(self.timing), 1)
        stat, ms, sample_rate = self.timing[0]
        self.assertEqual(stat, 'metrical.tests.test_metrical.spam')
        self.assertGreaterEqual(ms, 0)
        self.assertLess(ms, 10000)
        self.assertEqual(sample_rate, 1)

    def test_decorate_method(self):
        args = []

        from metrical import metricmethod

        class Spam:
            @metricmethod
            def f(self, x, y=2):
                args.append((x, y))

        self.assertEqual(Spam.f.__module__, 'metrical.tests.test_metrical')
        self.assertEqual(Spam.f.__name__, 'f')
        self.assertEqual(Spam.f.im_class, Spam)

        # Call with no statsd client configured.
        Spam().f(4, 5)
        self.assertEqual(args, [(4, 5)])
        del args[:]

        # Call with a statsd client configured.
        self._add_client()
        Spam().f(6, 1)
        self.assertEqual(args, [(6, 1)])
        self.assertEqual(self.updates,
                         [(['metrical.tests.test_metrical.Spam.f'], 1, 1)])
        self.assertEqual(len(self.timing), 1)
        stat, ms, sample_rate = self.timing[0]
        self.assertEqual(stat, 'metrical.tests.test_metrical.Spam.f')
        self.assertGreaterEqual(ms, 0)
        self.assertLess(ms, 10000)
        self.assertEqual(sample_rate, 1)

    def test_decorate_with_options(self):
        args = []

        from metrical import MetricDecorator

        @MetricDecorator('spammy', sample_rate=0.1, timing=False)
        def spam(x, y=2):
            args.append((x, y))

        self.assertEqual(spam.__module__, 'metrical.tests.test_metrical')
        self.assertEqual(spam.__name__, 'spam')

        # Call with no statsd client configured.
        spam(4, 5)
        self.assertEqual(args, [(4, 5)])
        del args[:]

        # Call with a statsd client configured.
        self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])
        self.assertEqual(self.updates, [(['spammy'], 1, 0.1)])
        self.assertEqual(len(self.timing), 0)
