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
    def close():
        """
        Release resources held by this object.

        .. versionadded:: 3.0
        """

    def timing(stat, value, rate=1, buf=None, rate_applied=False):
        """
        Log timing information in milliseconds.

            >>> client = StatsdClient()
            >>> client.timing('some.time', 500)
        """

    def gauge(stat, value, rate=1, buf=None, rate_applied=False):
        """
        Log a gauge value.

            >>> client = StatsdClient()
            >>> client.gauge('pool_size', 5)
        """

    def incr(stat, count=1, rate=1, buf=None, rate_applied=False):
        """
        Increment a counter.

            >>> client = StatsdClient()
            >>> client.incr('some.int')
            >>> client.incr('some.float', 0.5)
        """


    def decr(stat, count=1, rate=1, buf=None, rate_applied=False):
        """
        Decrement a counter.


            >>> client = StatsdClient()
            >>> client.decr('some.int')
        """


    def sendbuf(buf):
        """
        Send a UDP packet containing string lines.

        *buf* is a sequence of strings.
        """
