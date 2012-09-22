
try:
    import unittest2 as unittest
except ImportError:
    import unittest


class Test_statsd_config_functions(unittest.TestCase):

    def setUp(self):
        from perfmetrics import set_statsd_client
        set_statsd_client(None)

    tearDown = setUp

    def test_unconfigured(self):
        from perfmetrics import statsd_client
        self.assertIsNone(statsd_client())

    def test_configured_with_uri(self):
        from perfmetrics import set_statsd_client
        set_statsd_client('statsd://localhost:8125')
        from perfmetrics import StatsdClient
        from perfmetrics import statsd_client
        self.assertIsInstance(statsd_client(), StatsdClient)

    def test_configured_with_other_client(self):
        other_client = object()
        from perfmetrics import set_statsd_client
        set_statsd_client(other_client)
        from perfmetrics import statsd_client
        self.assertIs(statsd_client(), other_client)


class Test_statsd_client_from_uri(unittest.TestCase):

    def _call(self, uri):
        from perfmetrics import statsd_client_from_uri
        return statsd_client_from_uri(uri)

    def test_local_uri(self):
        client = self._call('statsd://localhost:8129')
        self.assertIsNotNone(client.udp_sock)

    def test_unsupported_uri(self):
        with self.assertRaises(ValueError):
            self._call('http://localhost:8125')

    def test_with_custom_gauge_suffix(self):
        client = self._call('statsd://localhost:8129?gauge_suffix=.spamalot')
        self.assertEqual(client.gauge_suffix, '.spamalot')


class TestMetric(unittest.TestCase):

    @property
    def _class(self):
        from perfmetrics import Metric
        return Metric

    @property
    def statsd_client_stack(self):
        from perfmetrics import statsd_client_stack
        return statsd_client_stack

    def setUp(self):
        self.statsd_client_stack.clear()

    tearDown = setUp

    def _add_client(self):
        self.changes = changes = []
        self.timing = timing = []
        self.sentbufs = sentbufs = []

        class DummyStatsdClient:
            def incr(self, stat, count=1, rate=1, buf=None,
                     rate_applied=False):
                changes.append((stat, count, rate, buf, rate_applied))
                if buf is not None:
                    buf.append('count_line')

            def timing(self, stat, ms, rate, buf=None,
                       rate_applied=False):
                timing.append((stat, ms, rate, buf, rate_applied))
                if buf is not None:
                    buf.append('timing_line')

            def sendbuf(self, buf):
                sentbufs.append(buf)

        self.statsd_client_stack.push(DummyStatsdClient())

    def test_ctor_with_defaults(self):
        obj = self._class()
        self.assertIsNone(obj.stat)
        self.assertEqual(obj.rate, 1)
        self.assertTrue(obj.count)
        self.assertTrue(obj.timing)

    def test_ctor_with_options(self):
        obj = self._class('spam.n.eggs', 0.1, count=False, timing=False)
        self.assertEqual(obj.stat, 'spam.n.eggs')
        self.assertEqual(obj.rate, 0.1)
        self.assertFalse(obj.count)
        self.assertFalse(obj.timing)

    def test_decorate_function(self):
        args = []
        metric = self._class()

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
        self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])

        stat, delta, rate, buf, rate_applied = self.changes[0]
        self.assertEqual(stat, __name__ + '.spam')
        self.assertEqual(delta, 1)
        self.assertEqual(rate, 1)
        self.assertEqual(buf, ['count_line', 'timing_line'])
        self.assertTrue(rate_applied)

        self.assertEqual(len(self.timing), 1)
        stat, ms, rate, _buf, rate_applied = self.timing[0]
        self.assertEqual(stat, __name__ + '.spam')
        self.assertGreaterEqual(ms, 0)
        self.assertLess(ms, 10000)
        self.assertEqual(rate, 1)
        self.assertTrue(rate_applied)

        self.assertEqual(self.sentbufs, [['count_line', 'timing_line']])

    def test_decorate_method(self):
        args = []
        metricmethod = self._class(method=True)

        class Spam:
            @metricmethod
            def f(self, x, y=2):
                args.append((x, y))

        self.assertEqual(Spam.f.__module__, __name__)
        self.assertEqual(Spam.f.__name__, 'f')

        # Call with no statsd client configured.
        Spam().f(4, 5)
        self.assertEqual(args, [(4, 5)])
        del args[:]

        # Call with a statsd client configured.
        self._add_client()
        Spam().f(6, 1)
        self.assertEqual(args, [(6, 1)])

        self.assertEqual(len(self.changes), 1)
        stat, delta, rate, buf, rate_applied = self.changes[0]
        self.assertEqual(stat, __name__ + '.Spam.f')
        self.assertEqual(delta, 1)
        self.assertEqual(rate, 1)
        self.assertEqual(buf, ['count_line', 'timing_line'])
        self.assertTrue(rate_applied)

        self.assertEqual(len(self.timing), 1)
        stat, ms, rate, _buf, rate_applied = self.timing[0]
        self.assertEqual(stat, __name__ + '.Spam.f')
        self.assertGreaterEqual(ms, 0)
        self.assertLess(ms, 10000)
        self.assertEqual(rate, 1)
        self.assertTrue(rate_applied)

        self.assertEqual(self.sentbufs, [['count_line', 'timing_line']])

    def test_decorate_without_timing(self):
        args = []
        Metric = self._class

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
        self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])

        self.assertEqual(len(self.changes), 1)
        stat, delta, rate, buf, rate_applied = self.changes[0]
        self.assertEqual(stat, 'spammy')
        self.assertEqual(delta, 1)
        self.assertEqual(rate, 0.01)
        self.assertIsNone(buf)
        self.assertTrue(rate_applied)

        self.assertEqual(len(self.timing), 0)
        self.assertEqual(self.sentbufs, [])

    def test_decorate_without_count(self):
        args = []
        Metric = self._class

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
        self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])
        self.assertEqual(self.changes, [])
        self.assertEqual(len(self.timing), 1)

        stat, ms, rate, buf, rate_applied = self.timing[0]
        self.assertEqual(stat, __name__ + '.spam')
        self.assertGreaterEqual(ms, 0)
        self.assertLess(ms, 10000)
        self.assertEqual(rate, 1)
        self.assertIsNone(buf)
        self.assertTrue(rate_applied)

        self.assertEqual(self.sentbufs, [])

    def test_decorate_with_neither_timing_nor_count(self):
        args = []
        Metric = self._class

        @Metric(count=False, timing=False)
        def spam(x, y=2):
            args.append((x, y))

        # Call with no statsd client configured.
        spam(4, 5)
        self.assertEqual(args, [(4, 5)])
        del args[:]

        # Call with a statsd client configured.
        self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])
        self.assertEqual(self.changes, [])
        self.assertEqual(len(self.timing), 0)

        self.assertEqual(self.sentbufs, [])

    def test_ignore_function_sample(self):
        args = []
        Metric = self._class

        @Metric(rate=0.99, random=lambda: 0.999)
        def spam(x, y=2):
            args.append((x, y))
            return 77

        self._add_client()
        self.assertEqual(77, spam(6, 1))

        # The function was called
        self.assertEqual(args, [(6, 1)])

        # No packets were sent because the random value was too high.
        self.assertFalse(self.changes)
        self.assertFalse(self.timing)
        self.assertFalse(self.sentbufs)

    def test_as_context_manager_with_stat_name(self):
        args = []
        Metric = self._class

        def spam(x, y=2):
            with Metric('thing-done'):
                args.append((x, y))

        # Call with no statsd client configured.
        spam(4, 5)
        self.assertEqual(args, [(4, 5)])
        del args[:]

        # Call with a statsd client configured.
        self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])

        stat, delta, rate, buf, rate_applied = self.changes[0]
        self.assertEqual(stat, 'thing-done')
        self.assertEqual(delta, 1)
        self.assertEqual(rate, 1)
        self.assertEqual(buf, ['count_line', 'timing_line'])
        self.assertTrue(rate_applied)

        self.assertEqual(len(self.timing), 1)
        stat, ms, rate, _buf, rate_applied = self.timing[0]
        self.assertEqual(stat, 'thing-done')
        self.assertGreaterEqual(ms, 0)
        self.assertLess(ms, 10000)
        self.assertEqual(rate, 1)
        self.assertTrue(rate_applied)

        self.assertEqual(self.sentbufs, [['count_line', 'timing_line']])

    def test_ignore_context_manager_sample(self):
        args = []
        Metric = self._class

        def spam(x, y=2):
            with Metric('thing-done', rate=0.99, random=lambda: 0.999):
                args.append((x, y))
                return 88

        self._add_client()
        self.assertEqual(88, spam(6, 716))

        # The function was called
        self.assertEqual(args, [(6, 716)])

        # No packets were sent because the random value was too high.
        self.assertFalse(self.changes)
        self.assertFalse(self.timing)
        self.assertFalse(self.sentbufs)

    def test_as_context_manager_without_stat_name(self):
        args = []
        Metric = self._class

        def spam(x, y=2):
            with Metric():
                args.append((x, y))

        self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])

        self.assertFalse(self.changes)
        self.assertFalse(self.timing)
        self.assertFalse(self.sentbufs)

    def test_as_context_manager_without_timing(self):
        args = []
        Metric = self._class

        def spam(x, y=2):
            with Metric('thing-done', timing=False):
                args.append((x, y))

        self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])

        self.assertEqual(len(self.changes), 1)

        stat, delta, rate, buf, rate_applied = self.changes[0]
        self.assertEqual(stat, 'thing-done')
        self.assertEqual(delta, 1)
        self.assertEqual(rate, 1)
        self.assertEqual(buf, ['count_line'])
        self.assertTrue(rate_applied)

        self.assertEqual(len(self.timing), 0)

        self.assertEqual(self.sentbufs, [['count_line']])

    def test_as_context_manager_without_count(self):
        args = []
        Metric = self._class

        def spam(x, y=2):
            with Metric('thing-done', count=False):
                args.append((x, y))

        # Call with a statsd client configured.
        self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])

        self.assertEqual(len(self.changes), 0)
        self.assertEqual(len(self.timing), 1)
        stat, ms, rate, _buf, rate_applied = self.timing[0]
        self.assertEqual(stat, 'thing-done')
        self.assertGreaterEqual(ms, 0)
        self.assertLess(ms, 10000)
        self.assertEqual(rate, 1)
        self.assertTrue(rate_applied)

        self.assertEqual(self.sentbufs, [['timing_line']])

    def test_as_context_manager_with_neither_count_nor_timing(self):
        args = []
        Metric = self._class

        def spam(x, y=2):
            with Metric('thing-done', count=False, timing=False):
                args.append((x, y))

        # Call with a statsd client configured.
        self._add_client()
        spam(6, 1)
        self.assertEqual(args, [(6, 1)])

        self.assertEqual(len(self.changes), 0)
        self.assertEqual(len(self.timing), 0)
        self.assertEqual(self.sentbufs, [])


class Test_includeme(unittest.TestCase):

    def _call(self, config):
        from perfmetrics import includeme
        includeme(config)

    def _make_config(self, statsd_uri):
        self.tweens = tweens = []

        class DummyRegistry:
            settings = {}
            if statsd_uri:
                settings['statsd_uri'] = statsd_uri

        class DummyConfig:
            registry = DummyRegistry()

            def add_tween(self, name):
                tweens.append(name)

        return DummyConfig()

    def test_without_statsd_uri(self):
        config = self._make_config(None)
        self._call(config)
        self.assertFalse(self.tweens)

    def test_with_statsd_uri(self):
        config = self._make_config('statsd://localhost:9999')
        self._call(config)
        self.assertEqual(self.tweens, ['perfmetrics.tween'])


class Test_tween(unittest.TestCase):

    def setUp(self):
        from perfmetrics import set_statsd_client, statsd_client_stack
        set_statsd_client(None)
        statsd_client_stack.clear()

    def _call(self, handler, registry):
        from perfmetrics import tween
        return tween(handler, registry)

    def _make_registry(self, statsd_uri):
        class DummyRegistry:
            settings = {'statsd_uri': statsd_uri}

        return DummyRegistry()

    def test_call_tween(self):
        clients = []

        def dummy_handler(request):
            from perfmetrics import statsd_client
            clients.append(statsd_client())
            return 'ok!'

        registry = self._make_registry('statsd://localhost:9999')
        tween = self._call(dummy_handler, registry)
        response = tween(object())
        self.assertEqual(response, 'ok!')
        self.assertEqual(len(clients), 1)
        from perfmetrics.statsd import StatsdClient
        self.assertIsInstance(clients[0], StatsdClient)


class Test_make_statsd_app(unittest.TestCase):

    def setUp(self):
        from perfmetrics import set_statsd_client, statsd_client_stack
        set_statsd_client(None)
        statsd_client_stack.clear()

    def _call(self, nextapp, statsd_uri):
        from perfmetrics import make_statsd_app
        return make_statsd_app(nextapp, None, statsd_uri)

    def test_without_statsd_uri(self):
        clients = []

        def dummy_app(environ, start_response):
            from perfmetrics import statsd_client
            clients.append(statsd_client())
            return ['ok.']

        app = self._call(dummy_app, '')
        response = app({}, None)
        self.assertEqual(response, ['ok.'])
        self.assertEqual(len(clients), 1)
        self.assertIsNone(clients[0])

    def test_with_statsd_uri(self):
        clients = []

        def dummy_app(environ, start_response):
            from perfmetrics import statsd_client
            clients.append(statsd_client())
            return ['ok.']

        app = self._call(dummy_app, 'statsd://localhost:9999')
        response = app({}, None)
        self.assertEqual(response, ['ok.'])
        self.assertEqual(len(clients), 1)
        from perfmetrics.statsd import StatsdClient
        self.assertIsInstance(clients[0], StatsdClient)
