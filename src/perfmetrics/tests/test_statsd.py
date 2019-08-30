# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest

from hamcrest import assert_that
from nti.testing.matchers import validly_provides

from perfmetrics.interfaces import IStatsdClient

# pylint:disable=protected-access

class MockSocket(object):
    def __init__(self, error=None):
        self.sent = []
        self.error = error

    def sendto(self, data, addr):
        if self.error is not None:
            raise self.error
        self.sent.append((data, addr))

    def close(self):
        pass


class TestBasics(unittest.TestCase):

    @property
    def _class(self):
        from perfmetrics.statsd import StatsdClient
        return StatsdClient

    def _makeOne(self, *args, **kwargs):
        kind = kwargs.pop('kind', None) or self._class
        inst = kind(*args, **kwargs)
        self.addCleanup(inst.close)
        return inst

    def test_implements(self):
        assert_that(self._makeOne(), validly_provides(IStatsdClient))

class TestNullStatsdClient(TestBasics):

    @property
    def _class(self):
        from perfmetrics.statsd import NullStatsdClient
        return NullStatsdClient

class TestStatsdClient(TestBasics):

    sent = ()

    def _make(self, patch_socket=True, error=None, prefix=''):
        obj = self._makeOne(prefix=prefix)

        if patch_socket:
            obj.udp_sock.close()
            obj.udp_sock = MockSocket(error)
            self.sent = obj.udp_sock.sent

        self.addCleanup(obj.close)
        return obj

    def test_ctor_with_defaults(self):
        obj = self._make(patch_socket=False)
        self.assertIsNotNone(obj.udp_sock)
        self.assertIsNotNone(obj.addr)
        self.assertEqual(obj.prefix, '')

    def test_ctor_with_options(self):
        obj = self._make(patch_socket=False, prefix='foo')
        self.assertIsNotNone(obj.udp_sock)
        self.assertIsNotNone(obj.addr)
        self.assertEqual(obj.prefix, 'foo.')

    def test_timing_with_rate_1(self):
        obj = self._make()
        obj.timing('some.thing', 750)
        self.assertEqual(self.sent, [(b'some.thing:750|ms', obj.addr)])

    def test_timing_with_rate_too_low(self):
        obj = self._make()
        obj.timing('some.thing', 750, rate=-1)
        self.assertEqual(self.sent, [])

    def test_timing_with_buf(self):
        obj = self._make()
        buf = []
        obj.timing('some.thing', 750, buf=buf)
        self.assertEqual(self.sent, [])
        self.assertEqual(buf, ['some.thing:750|ms'])

    def test_gauge_with_rate_1(self):
        obj = self._make()
        obj.gauge('some.thing', 50)
        self.assertEqual(self.sent, [(b'some.thing:50|g', obj.addr)])

    def test_gauge_with_rate_too_low(self):
        obj = self._make()
        obj.gauge('some.thing', 50, rate=-1)
        self.assertEqual(self.sent, [])

    def test_gauge_with_buf(self):
        obj = self._make()
        buf = []
        obj.gauge('some.thing', 50, buf=buf)
        self.assertEqual(buf, ['some.thing:50|g'])
        self.assertEqual(self.sent, [])

    def test_incr_with_one_metric(self):
        obj = self._make()
        obj.incr('some.thing')
        self.assertEqual(self.sent, [(b'some.thing:1|c', obj.addr)])

    def test_incr_with_two_metrics(self):
        obj = self._make()
        buf = []
        obj.incr('some.thing', buf=buf)
        obj.incr('other.thing', buf=buf)
        obj.sendbuf(buf)
        self.assertEqual(self.sent,
                         [(b'some.thing:1|c\nother.thing:1|c', obj.addr)])

    def test_incr_with_rate_too_low(self):
        obj = self._make()
        obj.incr('some.thing', rate=-1)
        self.assertEqual(self.sent, [])

    def test_decr(self):
        obj = self._make()
        obj.decr('some.thing')
        self.assertEqual(self.sent, [(b'some.thing:-1|c', obj.addr)])

    def test_incr_by_amount_with_one_metric(self):
        obj = self._make()
        obj.incr('some.thing', 51)
        self.assertEqual(self.sent, [(b'some.thing:51|c', obj.addr)])

    def test_incr_by_amount_with_two_metrics(self):
        obj = self._make()
        buf = []
        obj.incr('some.thing', 42, buf=buf)
        obj.incr('other.thing', -41, buf=buf)
        obj.sendbuf(buf)
        self.assertEqual(self.sent,
                         [(b'some.thing:42|c\nother.thing:-41|c', obj.addr)])

    def test_incr_with_rate_hit(self):
        obj = self._make()
        obj.random = lambda: 0.01
        obj.incr('some.thing', 51, rate=0.1)
        self.assertEqual(self.sent, [(b'some.thing:51|c|@0.1', obj.addr)])

    def test_incr_with_rate_miss(self):
        obj = self._make()
        obj.random = lambda: 0.99
        obj.incr('some.thing', 51, rate=0.1)
        self.assertEqual(self.sent, [])

    def test_send_with_ioerror(self):
        obj = self._make(error=IOError('synthetic'))
        obj._send('some.thing:41|g')
        self.assertEqual(self.sent, [])

    def test_sendbuf_with_ioerror(self):
        obj = self._make(error=IOError('synthetic'))
        obj.sendbuf(['some.thing:41|g'])
        self.assertEqual(self.sent, [])

    def test_sendbuf_with_empty_buf(self):
        obj = self._make()
        obj.sendbuf([])
        self.assertEqual(self.sent, [])

class TestStatsdClientMod(TestStatsdClient):

    @property
    def _class(self):
        from perfmetrics.statsd import StatsdClientMod
        return StatsdClientMod

    def _makeOne(self, *args, **kwargs):
        kwargs['kind'] = super(TestStatsdClientMod, self)._class
        wrapped = super(TestStatsdClientMod, self)._makeOne(*args, **kwargs)
        return self._class(wrapped, '%s')
