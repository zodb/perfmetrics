
try:
    import unittest2 as unittest
except ImportError:
    import unittest


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
        from metrical import StatsdClient
        from metrical import statsd_client
        self.assertIsInstance(statsd_client(), StatsdClient)

    def test_configured_with_other_client(self):
        other_client = object()
        from metrical import set_statsd_client
        set_statsd_client(other_client)
        from metrical import statsd_client
        self.assertIs(statsd_client(), other_client)


class Test_statsd_client_from_uri(unittest.TestCase):

    def _call(self, uri):
        from metrical import statsd_client_from_uri
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
