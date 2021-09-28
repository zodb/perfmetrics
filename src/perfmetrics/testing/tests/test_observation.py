#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"


import functools

import unittest

from hamcrest import none
from hamcrest import assert_that
from hamcrest import contains_exactly as contains
from hamcrest import is_
from hamcrest import has_length
from hamcrest import calling
from hamcrest import raises

from ..matchers import is_counter
from ..matchers import is_timer
from ..matchers import is_gauge
from ..matchers import is_set

from ..observation import Observation as Metric


class TestMetricParsing(unittest.TestCase):

    def test_invalid_packet(self):
        packet = 'junk'
        assert_that(calling(functools.partial(Metric.make_all, packet)),
                    raises(ValueError))

        packet = 'foo|bar|baz|junk'
        assert_that(calling(functools.partial(Metric.make_all, packet)),
                    raises(ValueError))

        packet = 'gorets:1|c|0.1'
        assert_that(calling(functools.partial(Metric.make_all, packet)),
                    raises(ValueError))

    def test_counter(self):
        packet = 'gorets:1|c'
        metric = Metric.make_all(packet)

        assert_that(metric, has_length(1))
        metric = metric[0]

        assert_that(metric, is_counter('gorets', '1', none()))

    def test_sampled_counter(self):
        packet = 'gorets:1|c|@0.1'
        metric = Metric.make_all(packet)

        assert_that(metric, has_length(1))
        metric = metric[0]

        assert_that(metric, is_counter('gorets', '1', 0.1))

    def test_timer(self):
        packet = 'glork:320|ms'
        metric = Metric.make_all(packet)

        assert_that(metric, has_length(1))
        metric = metric[0]

        assert_that(metric, is_timer('glork', '320'))

    def test_set(self):
        packet = 'glork:3|s'
        metric = Metric.make_all(packet)

        assert_that(metric, has_length(1))
        metric = metric[0]

        assert_that(metric, is_set('glork', '3'))

    def test_gauge(self):
        packet = 'gaugor:+333|g'
        metric = Metric.make_all(packet)

        assert_that(metric, has_length(1))
        metric = metric[0]

        assert_that(metric, is_gauge('gaugor', '+333'))

    def test_multi_metric(self):
        packet = 'gorets:1|c\nglork:320|ms\ngaugor:333|g\nuniques:765|s'
        metrics = Metric.make_all(packet)
        assert_that(metrics, contains(is_counter(),
                                      is_timer(),
                                      is_gauge(),
                                      is_set()))

    def test_metric_string(self):
        metric = Metric.make('gaugor:+333|g')
        assert_that(str(metric), is_('gaugor:+333|g'))

        packet = 'gorets:1|c|@0.1'
        metric = Metric.make_all(packet)[0]
        metric = Metric.make_all(str(metric))[0]

        assert_that(metric, is_counter('gorets', '1', 0.1))

    def test_factory(self):
        metric = Metric.make('gaugor:+333|g')
        assert_that(str(metric), is_('gaugor:+333|g'))

        assert_that(calling(functools.partial(Metric.make, 'gaugor:+333|g\ngaugor:+333|g')),
                    raises(ValueError))
