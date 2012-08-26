
try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestPyStatsdClient(unittest.TestCase):

    @property
    def _class(self):
        from metrical._pyimpl import StatsdClient
        return StatsdClient

    def _make(self, patch_socket=True, error=None):
        obj = self._class(gauge_suffix='.testsuffix')

        if patch_socket:
            self.sent = sent = []

            class DummySocket(object):
                def sendto(self, data, addr):
                    if error is not None:
                        raise error
                    sent.append((data, addr))

            obj.udp_sock = DummySocket()

        return obj

    def test_ctor(self):
        obj = self._make(patch_socket=False)
        self.assertIsNotNone(obj.udp_sock)
        self.assertIsNotNone(obj.addr)

    def test_timing_with_sample_rate_1(self):
        obj = self._make()
        obj.timing('some.thing', 750)
        self.assertEqual(self.sent, [('some.thing:750|ms', obj.addr)])

    def test_timing_with_sample_rate_too_low(self):
        obj = self._make()
        obj.timing('some.thing', 750, sample_rate=-1)
        self.assertEqual(self.sent, [])

    def test_gauge_with_sample_rate_1(self):
        obj = self._make()
        obj.gauge('some.thing', 50)
        self.assertEqual(self.sent, [('some.thing.testsuffix:50|g', obj.addr)])

    def test_gauge_with_sample_rate_too_low(self):
        obj = self._make()
        obj.gauge('some.thing', 50, sample_rate=-1)
        self.assertEqual(self.sent, [])

    def test_inc_with_one_metric(self):
        obj = self._make()
        obj.inc('some.thing')
        self.assertEqual(self.sent, [('some.thing:1|c', obj.addr)])

    def test_inc_with_two_metrics(self):
        obj = self._make()
        buf = []
        obj.inc('some.thing', buf=buf)
        obj.inc('other.thing', buf=buf)
        obj.sendbuf(buf)
        self.assertEqual(self.sent,
                         [('some.thing:1|c\nother.thing:1|c', obj.addr)])

    def test_inc_with_sample_rate_too_low(self):
        obj = self._make()
        obj.inc('some.thing', sample_rate=-1)
        self.assertEqual(sorted(self.sent), [])

    def test_dec(self):
        obj = self._make()
        obj.dec('some.thing')
        self.assertEqual(self.sent, [('some.thing:-1|c', obj.addr)])

    def test_change_with_one_metric(self):
        obj = self._make()
        obj.change('some.thing', 51)
        self.assertEqual(self.sent, [('some.thing:51|c', obj.addr)])

    def test_change_with_two_metrics(self):
        obj = self._make()
        buf = []
        obj.change('some.thing', 42, buf=buf)
        obj.change('other.thing', -41, buf=buf)
        obj.sendbuf(buf)
        self.assertEqual(self.sent,
                         [('some.thing:42|c\nother.thing:-41|c', obj.addr)])

    def test_send_with_ioerror(self):
        obj = self._make(error=IOError('synthetic'))
        obj.send('some.thing:41|g')
        self.assertEqual(self.sent, [])


class TestCStatsdClient(TestPyStatsdClient):

    @property
    def _class(self):
        from metrical._cimpl import StatsdClient
        return StatsdClient


class TestPyMetric(unittest.TestCase):

    @property
    def _class(self):
        from metrical._pyimpl import Metric
        return Metric

    @property
    def statsd_client_stack(self):
        from metrical import statsd_client_stack
        return statsd_client_stack

    def setUp(self):
        self.statsd_client_stack.clear()

    tearDown = setUp

    def _add_client(self):
        self.changes = changes = []
        self.timing = timing = []
        self.sentbufs = sentbufs = []

        class DummyStatsdClient:
            def change(self, stat, delta, sample_rate, buf=None):
                changes.append((stat, delta, sample_rate, buf))

            def timing(self, stat, ms, sample_rate, buf=None):
                timing.append((stat, ms, sample_rate, buf))

            def sendbuf(self, buf):
                sentbufs.append(buf)

        self.statsd_client_stack.push(DummyStatsdClient())

    def test_ctor_with_defaults(self):
        obj = self._class()
        self.assertIsNone(obj.stat)
        self.assertEqual(obj.sample_rate, 1)
        self.assertTrue(obj.count)
        self.assertTrue(obj.timing)

    def test_ctor_with_options(self):
        obj = self._class('spam.n.eggs', 0.1, count=False, timing=False)
        self.assertEqual(obj.stat, 'spam.n.eggs')
        self.assertEqual(obj.sample_rate, 0.1)
        self.assertFalse(obj.count)
        self.assertFalse(obj.timing)

    def test_decorate_function(self):
        args = []
        metric = self._class()

        @metric
        def spam(x, y=2):
            args.append((x, y))

        self.assertEqual(spam.__module__, 'metrical.tests.test_impls')
        self.assertEqual(spam.__name__, 'spam')

        # Call with no statsd client configured.
        spam(4, 5)
        self.assertEqual(args, [(4, 5)])
        del args[:]

        # Call with a statsd client configured.
        self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])
        self.assertEqual(self.changes,
                         [('metrical.tests.test_impls.spam', 1, 1, [])])
        self.assertEqual(len(self.timing), 1)
        stat, ms, sample_rate, _buf = self.timing[0]
        self.assertEqual(stat, 'metrical.tests.test_impls.spam')
        self.assertGreaterEqual(ms, 0)
        self.assertLess(ms, 10000)
        self.assertEqual(sample_rate, 1)

    def test_decorate_method(self):
        args = []
        metricmethod = self._class(method=True)

        class Spam:
            @metricmethod
            def f(self, x, y=2):
                args.append((x, y))

        self.assertEqual(Spam.f.__module__, 'metrical.tests.test_impls')
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
        self.assertEqual(self.changes,
                         [('metrical.tests.test_impls.Spam.f', 1, 1, [])])
        self.assertEqual(len(self.timing), 1)
        stat, ms, sample_rate, _buf = self.timing[0]
        self.assertEqual(stat, 'metrical.tests.test_impls.Spam.f')
        self.assertGreaterEqual(ms, 0)
        self.assertLess(ms, 10000)
        self.assertEqual(sample_rate, 1)

    def test_decorate_with_options(self):
        args = []
        Metric = self._class

        @Metric('spammy', sample_rate=0.1, timing=False)
        def spam(x, y=2):
            args.append((x, y))

        self.assertEqual(spam.__module__, 'metrical.tests.test_impls')
        self.assertEqual(spam.__name__, 'spam')

        # Call with no statsd client configured.
        spam(4, 5)
        self.assertEqual(args, [(4, 5)])
        del args[:]

        # Call with a statsd client configured.
        self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])
        self.assertEqual(self.changes, [('spammy', 1, 0.1, None)])
        self.assertEqual(len(self.timing), 0)


class TestCMetric(TestPyMetric):

    @property
    def _class(self):
        from metrical._cimpl import Metric
        return Metric
