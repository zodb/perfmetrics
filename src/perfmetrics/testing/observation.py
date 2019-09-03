#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

#: The statsd metric kind for Gauges
OBSERVATION_KIND_GAUGE = 'g'

#: The statsd metric kind for Counters
OBSERVATION_KIND_COUNTER = 'c'

#: The statsd metric kind for Sets
OBSERVATION_KIND_SET = 's'

#: The statsd metric kind for Timers
OBSERVATION_KIND_TIMER = 'ms'


def _parse_sampling_data(data):
    """
    Parses sampling rate from the provided packet part *data*.

    Raises a `ValueError` if the packet part is invalid sampling data
    """
    if not data.startswith('@'):
        raise ValueError('Expected "@" in sampling data. %s' % data)
    return float(data[1:])


def _as_metric(metric_data):
    """
    Parses a single metric packet, *metric_data*, in to a `Metric`.

    Metrics take the form of <name>:<value>|<type>(|@<sampling_rate>)

    A `ValueError` is raised for invalid data
    """

    sampling = None
    name = None
    value = None
    kind = None
    parts = metric_data.split('|')
    if len(parts) < 2 or len(parts) > 3:
        raise ValueError('Unexpected metric data %s. Wrong number of parts' % metric_data)

    if len(parts) == 3:
        sampling_data = parts.pop(-1)
        sampling = _parse_sampling_data(sampling_data)

    kind = parts[1]
    name, value = parts[0].split(':')

    return Observation(name, value, kind, sampling_rate=sampling)


def _as_metrics(data):
    """
    Parses the statsd *data* packet to a _list_ of metrics.

    .. seealso:: https://github.com/etsy/statsd/blob/master/docs/metric_types.md
    """
    metrics = []

    # Multi metric packets are seperated by newlines
    for metric_data in data.split('\n'):
        metrics.append(_as_metric(metric_data))
    return metrics


class Observation(object):
    """
    The representation of a single statsd metric.
    """

    #: The metric name
    name = None

    #: The value provided for the metric
    value = None

    #: The statsd code for the type of metric. e.g. one of the ``METRIC_*_KIND`` constants
    kind = None

    #: The rate with which this event has been sampled from (optional)
    sampling_rate = None

    def __init__(self, name, value, kind, sampling_rate=None):
        self.name = name
        self.value = value
        self.sampling_rate = sampling_rate
        self.kind = kind

    @classmethod
    def make(cls, packet):
        """
        Creates a metric from the provided statsd *packet*.

        :raises ValueError: if *packet* is a multi metric packet or
                 otherwise invalid.
        """
        metrics = cls.make_all(packet)
        if len(metrics) != 1:
            raise ValueError('Must supply a single metric packet. %s supplied' % packet)
        return metrics[0]

    @classmethod
    def make_all(cls, packet):
        """
        Makes a list of metrics from the provided statsd *packet*.

        Like `make` but supports multi metric packets
        """
        return _as_metrics(packet)

    def __str__(self):
        sampling_string = '|@%g' % self.sampling_rate if self.sampling_rate is not None else ''
        return '%s:%s|%s%s' % (self.name, self.value, self.kind, sampling_string)

    def __repr__(self):
        return "%s(name=%r, value=%r, kind=%r, sampling_rate=%r)" % (
            self.__class__.__name__,
            self.name, self.value, self.kind, self.sampling_rate
        )
