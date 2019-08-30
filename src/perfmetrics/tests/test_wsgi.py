# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest

class Test_make_statsd_app(unittest.TestCase):

    def setUp(self):
        from perfmetrics import set_statsd_client, statsd_client_stack
        set_statsd_client(None)
        statsd_client_stack.clear()

    def _call(self, nextapp, statsd_uri):
        from perfmetrics import make_statsd_app
        app = make_statsd_app(nextapp, None, statsd_uri)
        if hasattr(app, 'statsd_client'):
            self.addCleanup(app.statsd_client.close)
        return app

    def test_without_statsd_uri(self):
        clients = []

        def dummy_app(_environ, _start_response):
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

        def dummy_app(_environ, _start_response):
            from perfmetrics import statsd_client
            clients.append(statsd_client())
            return ['ok.']

        app = self._call(dummy_app, 'statsd://localhost:9999')
        response = app({}, None)
        self.assertEqual(response, ['ok.'])
        self.assertEqual(len(clients), 1)
        from perfmetrics.statsd import StatsdClient
        self.assertIsInstance(clients[0], StatsdClient)
