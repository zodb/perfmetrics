# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

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
        client = statsd_client()
        self.addCleanup(client.close)
        self.assertIsInstance(client, StatsdClient)

    def test_configured_with_other_client(self):
        other_client = object()
        from perfmetrics import set_statsd_client
        set_statsd_client(other_client)
        from perfmetrics import statsd_client
        self.assertIs(statsd_client(), other_client)


class Test_statsd_client_from_uri(unittest.TestCase):

    def _call(self, uri):
        from perfmetrics import statsd_client_from_uri
        client = statsd_client_from_uri(uri)
        self.addCleanup(client.close)
        return client

    def test_local_uri(self):
        client = self._call('statsd://localhost:8129')
        self.assertIsNotNone(client.udp_sock)

    def test_unsupported_uri(self):
        with self.assertRaises(ValueError):
            self._call('http://localhost:8125')

    def test_with_custom_prefix(self):
        client = self._call('statsd://localhost:8129?prefix=spamalot')
        self.assertEqual(client.prefix, 'spamalot.')
