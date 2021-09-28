#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import doctest
import os
import unittest

from hamcrest import assert_that
from hamcrest import contains_exactly as contains

from hamcrest import has_length
from hamcrest import has_properties
from hamcrest import has_property

from ...tests import is_true

from ...tests.test_statsd import TestBasics

from .. import FakeStatsDClient as MockStatsDClient

from ..observation import OBSERVATION_KIND_COUNTER as METRIC_COUNTER_KIND
from ..observation import OBSERVATION_KIND_GAUGE as METRIC_GAUGE_KIND
from ..observation import OBSERVATION_KIND_SET as METRIC_SET_KIND
from ..observation import OBSERVATION_KIND_TIMER as METRIC_TIMER_KIND

class TestMockStatsDClient(TestBasics):

    _class = MockStatsDClient

    def setUp(self):
        self.client = self._makeOne()

    def test_true_initially(self):
        assert_that(self.client, is_true())

    def test_tracks_metrics(self):
        self.client.incr('mycounter')
        self.client.gauge('mygauge', 5)
        self.client.timing('mytimer', 3003)
        self.client.set_add('myset', 42)

        assert_that(self.client, has_length(4))

        counter, gauge, timer, Set = self.client.observations

        assert_that(counter, has_properties('name', 'mycounter',
                                            'value', '1',
                                            'kind', METRIC_COUNTER_KIND))

        assert_that(gauge, has_properties('name', 'mygauge',
                                          'value', '5',
                                          'kind', METRIC_GAUGE_KIND))

        assert_that(timer, has_properties(
            'name', 'mytimer',
            'value', '3003',
            'kind', METRIC_TIMER_KIND
        ))

        assert_that(Set, has_properties(
            'name', 'myset',
            'value', '42',
            'kind', METRIC_SET_KIND
        ))

    def test_clear(self):
        self.client.incr('mycounter')
        assert_that(self.client, has_length(1))
        assert_that(self.client, is_true())

        self.client.clear()
        assert_that(self.client, has_length(0))
        assert_that(self.client, is_true())

    def test_tracks_multimetrics(self):
        packet = 'gorets:1|c\nglork:320|ms\ngaugor:333|g\nuniques:765|s'
        self.client._send(packet)

        assert_that(self.client, has_length(4))
        assert_that(self.client.packets, contains(packet))

        assert_that(self.client.observations,
                    contains(has_property('kind', METRIC_COUNTER_KIND),
                             has_property('kind', METRIC_TIMER_KIND),
                             has_property('kind', METRIC_GAUGE_KIND),
                             has_property('kind', METRIC_SET_KIND)))

def test_suite():
    root = this_dir = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(root, 'setup.py')):
        prev, root = root, os.path.dirname(root)
        if root == prev:
            # We seem to be installed out of tree. Are we working in the
            # right directory at least?
            if os.path.exists('setup.py'): # pragma: no cover
                root = os.path.dirname(os.path.abspath('setup.py'))
                break
            # Let's avoid infinite loops at root
            raise AssertionError('could not find my setup.py')
    docs = os.path.join(root, 'docs')
    testing_rst = os.path.join(docs, 'testing.rst')

    optionflags = (
        doctest.NORMALIZE_WHITESPACE
        | doctest.ELLIPSIS
        | doctest.IGNORE_EXCEPTION_DETAIL
    )

    # Can't pass absolute paths to DocFileSuite, needs to be
    # module relative
    testing_rst = os.path.relpath(testing_rst, this_dir)

    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromName(__name__),
        doctest.DocFileSuite(
            testing_rst,
            optionflags=optionflags
        ),
    ))
