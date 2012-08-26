
try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestStatsdClient(unittest.TestCase):

    @property
    def _class(self):
        from metrical.statsdclient import StatsdClient
        return StatsdClient

    def _make(self, patch_socket=True, error=None):
        obj = self._class()

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
        self.assertEqual(self.sent, [('some.thing:50|g', obj.addr)])

    def test_gauge_with_sample_rate_too_low(self):
        obj = self._make()
        obj.gauge('some.thing', 50, sample_rate=-1)
        self.assertEqual(self.sent, [])

    def test_increment_with_one_metric(self):
        obj = self._make()
        obj.increment('some.thing')
        self.assertEqual(self.sent, [('some.thing:1|c', obj.addr)])

    def test_increment_with_two_metrics(self):
        obj = self._make()
        obj.increment(['some.thing', 'other.thing'])
        self.assertEqual(sorted(self.sent), [('other.thing:1|c', obj.addr),
                                             ('some.thing:1|c', obj.addr)])

    def test_increment_with_sample_rate_too_low(self):
        obj = self._make()
        obj.increment(['some.thing', 'other.thing'], sample_rate=-1)
        self.assertEqual(sorted(self.sent), [])

    def test_decrement(self):
        obj = self._make()
        obj.decrement('some.thing')
        self.assertEqual(self.sent, [('some.thing:-1|c', obj.addr)])

    def test_update_stats_with_one_metric(self):
        obj = self._make()
        obj.update_stats('some.thing', 51)
        self.assertEqual(self.sent, [('some.thing:51|c', obj.addr)])

    def test_update_stats_with_two_metrics(self):
        obj = self._make()
        obj.update_stats(['some.thing', 'other.thing'], 42)
        self.assertEqual(sorted(self.sent), [('other.thing:42|c', obj.addr),
                                             ('some.thing:42|c', obj.addr)])

    def test_send_with_excluded_sample(self):
        obj = self._make()
        obj.random = lambda: 0.2
        obj.send({'some.thing': '41|g'}, sample_rate=0.1)
        self.assertEqual(self.sent, [])

    def test_send_with_included_sample(self):
        obj = self._make()
        obj.random = lambda: 0.05
        obj.send({'some.thing': '41|g'}, sample_rate=0.1)
        self.assertEqual(self.sent, [('some.thing:41|g|@0.1', obj.addr)])

    def test_send_with_ioerror(self):
        obj = self._make(error=IOError('synthetic'))
        obj.send({'some.thing': '41|g'})
        self.assertEqual(self.sent, [])
