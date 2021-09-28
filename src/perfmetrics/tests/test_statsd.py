# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest

from zope.interface import verify

from hamcrest import assert_that

from perfmetrics.interfaces import IStatsdClient

from . import validly_provides
from . import is_true
from . import implements


# pylint:disable=protected-access
# pylint:disable=too-many-public-methods

class MockSocket(object):
    def __init__(self, error=None):
        self.sent = []
        self.error = error

    def sendto(self, data, addr):
        if self.error is not None:
            raise self.error # pylint:disable=raising-bad-type
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

    def test_provides(self):
        assert_that(self._makeOne(), validly_provides(IStatsdClient))

    def test_implements(self):
        kind = type(self._makeOne())
        assert_that(kind, implements(IStatsdClient))
        # That just checks the declaration of the interface, it doesn't
        # do a static check of attributes.
        assert_that(
            verify.verifyClass(IStatsdClient, kind),
            is_true())

    def test_true(self):
        assert_that(self._makeOne(), is_true())

class TestNullStatsdClient(TestBasics):

    @property
    def _class(self):
        from perfmetrics.statsd import NullStatsdClient
        return NullStatsdClient

class TestStatsdClient(TestBasics):

    sent = ()

    # The main stat name, as entered by the application
    STAT_NAME = 'some.thing'
    # The main stat name, as sent on the wire
    STAT_NAMEB = b'some.thing'
    STAT_NAME2 = 'other.thing'
    STAT_NAME2B = b'other.thing'

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
        obj.timing(self.STAT_NAME, 750)
        self.assertEqual(self.sent, [(self.STAT_NAMEB + b':750|ms', obj.addr)])

    def test_timing_with_rate_too_low(self):
        obj = self._make()
        obj.timing(self.STAT_NAME, 750, rate=-1)
        self.assertEqual(self.sent, [])

    def test_timing_with_buf(self):
        obj = self._make()
        buf = []
        obj.timing(self.STAT_NAME, 750, buf=buf)
        self.assertEqual(self.sent, [])
        obj.sendbuf(buf)
        self.assertEqual(self.sent, [(self.STAT_NAMEB + b':750|ms', obj.addr)])

    def test_gauge_with_rate_1(self):
        obj = self._make()
        obj.gauge(self.STAT_NAME, 50)
        self.assertEqual(self.sent, [(self.STAT_NAMEB + b':50|g', obj.addr)])

    def test_gauge_with_rate_too_low(self):
        obj = self._make()
        obj.gauge(self.STAT_NAME, 50, rate=-1)
        self.assertEqual(self.sent, [])

    def test_gauge_with_buf(self):
        obj = self._make()
        buf = []
        obj.gauge(self.STAT_NAME, 50, buf=buf)
        self.assertEqual(self.sent, [])
        obj.sendbuf(buf)
        self.assertEqual(self.sent, [(self.STAT_NAMEB + b':50|g', obj.addr)])

    def test_incr_with_one_metric(self):
        obj = self._make()
        obj.incr(self.STAT_NAME)
        self.assertEqual(self.sent, [(self.STAT_NAMEB + b':1|c', obj.addr)])

    def test_incr_with_two_metrics(self):
        obj = self._make()
        buf = []
        obj.incr(self.STAT_NAME, buf=buf)
        obj.incr(self.STAT_NAME2, buf=buf)
        obj.sendbuf(buf)
        self.assertEqual(self.sent,
                         [(self.STAT_NAMEB + b':1|c\n' + self.STAT_NAME2B + b':1|c', obj.addr)])

    def test_incr_with_rate_too_low(self):
        obj = self._make()
        obj.incr(self.STAT_NAME, rate=-1)
        self.assertEqual(self.sent, [])

    def test_decr(self):
        obj = self._make()
        obj.decr(self.STAT_NAME)
        self.assertEqual(self.sent, [(self.STAT_NAMEB + b':-1|c', obj.addr)])

    def test_incr_by_amount_with_one_metric(self):
        obj = self._make()
        obj.incr(self.STAT_NAME, 51)
        self.assertEqual(self.sent, [(self.STAT_NAMEB + b':51|c', obj.addr)])

    def test_incr_by_amount_with_two_metrics(self):
        obj = self._make()
        buf = []
        obj.incr(self.STAT_NAME, 42, buf=buf)
        obj.incr(self.STAT_NAME2, -41, buf=buf)
        obj.sendbuf(buf)
        self.assertEqual(self.sent,
                         [(self.STAT_NAMEB + b':42|c\n' + self.STAT_NAME2B + b':-41|c', obj.addr)])

    def test_incr_with_rate_hit(self):
        obj = self._make()
        obj.random = lambda: 0.01
        obj.incr(self.STAT_NAME, 51, rate=0.1)
        self.assertEqual(self.sent, [(self.STAT_NAMEB + b':51|c|@0.1', obj.addr)])

    def test_incr_with_rate_miss(self):
        obj = self._make()
        obj.random = lambda: 0.99
        obj.incr(self.STAT_NAME, 51, rate=0.1)
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

    def test_set_add(self):
        obj = self._make()
        obj.set_add(self.STAT_NAME, 42)
        self.assertEqual(self.sent, [(self.STAT_NAMEB + b':42|s', obj.addr)])

    def test_set_add_with_buf(self):
        obj = self._make()
        buf = []
        obj.set_add(self.STAT_NAME, 42, buf=buf)
        obj.set_add(self.STAT_NAME2, 23, buf=buf)
        obj.sendbuf(buf)
        self.assertEqual(self.sent,
                         [(self.STAT_NAMEB + b':42|s\n' + self.STAT_NAME2B + b':23|s', obj.addr)])


    def test_set_add_with_rate_hit(self):
        obj = self._make()
        obj.random = lambda: 0.01
        obj.set_add(self.STAT_NAME, 51, rate=0.1)
        self.assertEqual(self.sent, [(self.STAT_NAMEB + b':51|s', obj.addr)])

    def test_set_add_with_rate_miss(self):
        obj = self._make()
        obj.random = lambda: 0.99
        obj.set_add(self.STAT_NAME, 51, rate=0.1)
        self.assertEqual(self.sent, [])

class TestStatsdClientMod(TestStatsdClient):

    STAT_NAMEB = b'wrap.some.thing'
    STAT_NAME2B = b'wrap.other.thing'

    @property
    def _class(self):
        from perfmetrics.statsd import StatsdClientMod
        return StatsdClientMod

    def _makeOne(self, *args, **kwargs):
        from perfmetrics.statsd import StatsdClient
        kwargs['kind'] = super(TestStatsdClientMod, self)._class
        wrapped = super(TestStatsdClientMod, self)._makeOne(*args, **kwargs)
        assert type(wrapped) is StatsdClient # pylint:disable=unidiomatic-typecheck
        # Be sure to use a format string that alters the stat name so we
        # can prove the method is getting called. With __getattr__ there, we could
        # silently call through to the wrapped class without knowing it.
        return self._class(wrapped, 'wrap.%s')
