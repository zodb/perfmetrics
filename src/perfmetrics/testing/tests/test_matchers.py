#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"


import unittest

from hamcrest import all_of
from hamcrest import assert_that
from hamcrest import contains_string
from hamcrest import is_not
from hamcrest import none

from hamcrest.core.string_description import StringDescription

from ..matchers import is_observation as is_metric
from ..matchers import is_counter
from ..matchers import is_gauge
from ..matchers import is_set
from ..matchers import is_timer

from ..observation import Observation as Metric


class TestIsMetric(unittest.TestCase):

    def setUp(self):
        self.counter = Metric.make('foo:1|c')
        self.timer = Metric.make('foo:100|ms|@0.1')
        self.set = Metric.make('foo:bar|s')
        self.gauge = Metric.make('foo:200|g')

    def test_is_metric(self):
        assert_that(self.counter, is_metric('c'))
        assert_that(self.counter, is_metric('c', 'foo'))
        assert_that(self.counter, is_metric('c', 'foo', '1'))
        assert_that(self.counter, is_metric('c', 'foo', '1', None))

    def test_non_metric(self):
        assert_that(object(), is_not(is_metric()))

    def test_is_counter(self):
        assert_that(self.counter, is_counter())

    def test_is_gauge(self):
        assert_that(self.gauge, is_gauge())

    def test_is_set(self):
        assert_that(self.set, is_set())

    def test_is_timer(self):
        assert_that(self.timer, is_timer())

    def test_bad_kind(self):
        assert_that(self.counter, is_not(is_timer()))

    def test_bad_name(self):
        assert_that(self.counter, is_not(is_counter('bar')))

    def test_bad_value(self):
        assert_that(self.counter, is_not(is_counter('foo', '2')))

    def test_bad_sampling(self):
        assert_that(self.timer, is_not(is_counter('foo', '100', None)))

    def test_failure_error(self):
        desc = StringDescription()
        matcher = is_counter('foo', '1', 0.1)
        matcher.describe_to(desc)
        desc = str(desc)
        # Strip internal newlines, which vary between
        # hamcrest versions. Also, the exact text varies too;
        # beginning with 1.10, the has_properties matcher we use internally is
        # less verbose by default and so we get a string like:
        #   an object with properties kind matching c and name matching foo
        # where before it was something like
        #  an object with property kind matching c
        #  and an object with property name matching foo

        desc = desc.replace('\n', '')
        assert_that(
            desc,
            all_of(
                contains_string(
                    "(an instance of Observation and "),
                contains_string(
                    "'kind' matching 'c'"),
                contains_string(
                    "'name' matching 'foo'"),
                contains_string(
                    "'value' matching '1'"),
                contains_string(
                    "'sampling_rate' matching <0.1>"
                )
            )
        )


    def test_components_can_be_matchers(self):
        assert_that(self.counter, is_metric('c', 'foo', '1', none()))
        assert_that(self.timer, is_not(is_metric('ms', 'foo', '100', none())))
