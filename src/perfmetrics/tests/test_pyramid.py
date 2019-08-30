# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest


class MockRegistry(object):
    def __init__(self, statsd_uri=None):
        self.settings = {}
        if statsd_uri:
            self.settings['statsd_uri'] = statsd_uri

class MockConfig(object):
    def __init__(self, statsd_uri=None):
        self.registry = MockRegistry(statsd_uri)
        self.tweens = []

    def add_tween(self, name):
        self.tweens.append(name)


class Test_includeme(unittest.TestCase):

    def _call(self, config):
        from perfmetrics import includeme
        includeme(config)

    def _make_config(self, statsd_uri):
        return MockConfig(statsd_uri)

    def test_without_statsd_uri(self):
        config = self._make_config(None)
        self._call(config)
        self.assertFalse(config.tweens)

    def test_with_statsd_uri(self):
        config = self._make_config('statsd://localhost:9999')
        self._call(config)
        self.assertEqual(config.tweens, ['perfmetrics.tween'])


class Test_tween(unittest.TestCase):

    def setUp(self):
        from perfmetrics import set_statsd_client, statsd_client_stack
        set_statsd_client(None)
        statsd_client_stack.clear()

    def _call(self, handler, registry):
        from perfmetrics import tween
        return tween(handler, registry)

    def _make_registry(self, statsd_uri):
        return MockRegistry(statsd_uri)

    def test_call_tween(self):
        clients = []

        def dummy_handler(_request):
            from perfmetrics import statsd_client
            client = statsd_client()
            self.addCleanup(client.close)
            clients.append(client)
            return 'ok!'

        registry = self._make_registry('statsd://localhost:9999')
        tween = self._call(dummy_handler, registry)
        response = tween(object())
        self.assertEqual(response, 'ok!')
        self.assertEqual(len(clients), 1)
        from perfmetrics.statsd import StatsdClient
        self.assertIsInstance(clients[0], StatsdClient)
