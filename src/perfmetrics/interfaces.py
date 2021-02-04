# -*- coding: utf-8 -*-
"""
Interfaces for perfmetrics.

If zope.interface is not installed, this file is merely documentation.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# pylint:disable=no-self-argument,no-method-argument

try:
    from zope import interface
except ImportError: # pragma: no cover
    class Interface(object):
        pass
    class Attribute(object):
        def __init__(self, descr):
            self.descr = descr
    class implementer(object):
        def __init__(self, *ifaces):
            pass
        def __call__(self, cls):
            return cls
else:
    Interface = interface.Interface
    Attribute = interface.Attribute
    implementer = interface.implementer


class IStatsdClient(Interface):
    """
    Interface to communicate with a StatsD server.

    Most of the methods below have optional ``rate``, ``rate_applied``,
    and ``buf`` parameters.  The ``rate`` parameter, when set to a value
    less than 1, causes StatsdClient to send a random sample of packets rather
    than every packet.  The ``rate_applied`` parameter, if true, informs
    ``StatsdClient`` that the sample rate has already been applied and the
    packet should be sent regardless of the specified sample rate.

    If the ``buf`` parameter is a list, StatsdClient
    appends the packet contents to the ``buf`` list rather than send the
    packet, making it possible to send multiple updates in a single packet.
    Keep in mind that the size of UDP packets is limited (the limit varies
    by the network, but 1000 bytes is usually a good guess) and any extra
    bytes will be ignored silently.

    """
    def close():
        """
        Release resources (sockets) held by this object.

        .. versionadded:: 3.0
        """

    def timing(stat, value, rate=1, buf=None, rate_applied=False):
        """
        Log timing information in milliseconds.

        *stat* is the name of the metric to record and *value* is
        the timing measurement in milliseconds. Note that Statsd
        maintains several data points for each timing metric, so
        timing metrics can take more disk space than counters or
        gauges.
        """

    def gauge(stat, value, rate=1, buf=None, rate_applied=False):
        """
        Update a gauge value.

        *stat* is the name of the metric to record and *value* is
        the new gauge value. A gauge represents a persistent value
        such as a pool size. Because gauges from different machines
        often conflict, a suffix is usually applied to gauge names;
        this may be done manually or with `MetricMod`.
        """

    def incr(stat, count=1, rate=1, buf=None, rate_applied=False):
        """
        Increment a counter by *count*.

        Note that Statsd clears all counter values every time it sends
        the metrics to Graphite, which usually happens every 10
        seconds. If you need a persistent value, it may be more
        appropriate to use a gauge instead of a counter.
        """

    def decr(stat, count=1, rate=1, buf=None, rate_applied=False):
        """
        Decrement a counter.

        This is the opposite of :meth:`incr`.
        """

    def set_add(stat, value, rate=1, buf=None, rate_applied=False):
        """
        Add a *value* to the set named by *stat*.

        A StatsD set counts the unique occurrences of events (values)
        between flushes.

        For example, if you wanted to count the number of different
        users logging in to an application within the sampling period,
        you could use something like::

            def on_login(user_id):
                client.set_add("logged_in_users", user_id)

        While this method accepts the *rate* parameter, it may be less
        useful here since the point is to let the StatsD server collect
        unique events automatically, and it can't do that if some events
        are dropped, making it only an estimate.

        .. versionadded:: 3.1.0
        """


    def sendbuf(buf):
        """
        Send a UDP packet containing string lines.

        *buf* is a sequence of strings.
        """
