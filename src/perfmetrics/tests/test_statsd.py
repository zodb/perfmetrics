
try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestStatsdClient(unittest.TestCase):

    @property
    def _class(self):
        from perfmetrics.statsd import StatsdClient
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
        self.assertEqual(self.sent, [(b'some.thing:750|ms', obj.addr)])

    def test_timing_with_sample_rate_too_low(self):
        obj = self._make()
        obj.timing('some.thing', 750, sample_rate=-1)
        self.assertEqual(self.sent, [])

    def test_timing_with_buf(self):
        obj = self._make()
        buf = []
        obj.timing('some.thing', 750, buf=buf)
        self.assertEqual(self.sent, [])
        self.assertEqual(buf, ['some.thing:750|ms'])

    def test_gauge_with_sample_rate_1(self):
        obj = self._make()
        obj.gauge('some.thing', 50)
        self.assertEqual(self.sent, [(b'some.thing.testsuffix:50|g', obj.addr)])

    def test_gauge_with_sample_rate_too_low(self):
        obj = self._make()
        obj.gauge('some.thing', 50, sample_rate=-1)
        self.assertEqual(self.sent, [])

    def test_gauge_with_buf(self):
        obj = self._make()
        buf = []
        obj.gauge('some.thing', 50, buf=buf)
        self.assertEqual(buf, ['some.thing.testsuffix:50|g'])
        self.assertEqual(self.sent, [])

    def test_inc_with_one_metric(self):
        obj = self._make()
        obj.inc('some.thing')
        self.assertEqual(self.sent, [(b'some.thing:1|c', obj.addr)])

    def test_inc_with_two_metrics(self):
        obj = self._make()
        buf = []
        obj.inc('some.thing', buf=buf)
        obj.inc('other.thing', buf=buf)
        obj.sendbuf(buf)
        self.assertEqual(self.sent,
                         [(b'some.thing:1|c\nother.thing:1|c', obj.addr)])

    def test_inc_with_sample_rate_too_low(self):
        obj = self._make()
        obj.inc('some.thing', sample_rate=-1)
        self.assertEqual(self.sent, [])

    def test_dec(self):
        obj = self._make()
        obj.dec('some.thing')
        self.assertEqual(self.sent, [(b'some.thing:-1|c', obj.addr)])

    def test_change_with_one_metric(self):
        obj = self._make()
        obj.change('some.thing', 51)
        self.assertEqual(self.sent, [(b'some.thing:51|c', obj.addr)])

    def test_change_with_two_metrics(self):
        obj = self._make()
        buf = []
        obj.change('some.thing', 42, buf=buf)
        obj.change('other.thing', -41, buf=buf)
        obj.sendbuf(buf)
        self.assertEqual(self.sent,
                         [(b'some.thing:42|c\nother.thing:-41|c', obj.addr)])

    def test_change_with_sample_rate_hit(self):
        obj = self._make()
        obj.random = lambda: 0.01
        obj.change('some.thing', 51, sample_rate=0.1)
        self.assertEqual(self.sent, [(b'some.thing:51|c|@0.1', obj.addr)])

    def test_change_with_sample_rate_miss(self):
        obj = self._make()
        obj.random = lambda: 0.99
        obj.change('some.thing', 51, sample_rate=0.1)
        self.assertEqual(self.sent, [])

    def test_send_with_ioerror(self):
        obj = self._make(error=IOError('synthetic'))
        obj.send('some.thing:41|g')
        self.assertEqual(self.sent, [])

    def test_sendbuf_with_ioerror(self):
        obj = self._make(error=IOError('synthetic'))
        obj.sendbuf(['some.thing:41|g'])
        self.assertEqual(self.sent, [])
