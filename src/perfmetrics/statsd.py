# -*- coding: utf-8 -*-
"""
Statsd client implementations.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import random
import socket

try:
    # Python 3
    from urllib.parse import urlsplit
    from urllib.parse import parse_qsl
    from urllib.parse import uses_query

    basestring = str

except ImportError: # pragma: no cover
    # Python 2
    from urlparse import urlsplit
    from urlparse import parse_qsl
    from urlparse import uses_query

from .interfaces import IStatsdClient
from .interfaces import implementer

logger = logging.getLogger(__name__)

__all__ = [
    'StatsdClient',
    'StatsdClientMod',
    'NullStatsdClient',
    'statsd_client_from_uri',
]

if 'statsd' not in uses_query:  # pragma: no cover
    uses_query.append('statsd')

def statsd_client_from_uri(uri):
    """
    Create and return :class:`perfmetrics.statsd.StatsdClient`.

    A typical URI is ``statsd://localhost:8125``. An optional query
    parameter is ``prefix``. The default prefix is an empty string.

    """
    parts = urlsplit(uri)
    if parts.scheme != 'statsd':
        raise ValueError("URI scheme not supported: %s" % uri)

    kw = {}
    if parts.query:
        kw.update(parse_qsl(parts.query))
    return StatsdClient(parts.hostname, parts.port, **kw)


@implementer(IStatsdClient)
class StatsdClient(object):
    """
    Send packets to statsd.

    Default implementation of :class:`perfmetrics.interfaces.IStatsdClient`.

    Derived from statsd.py by Steve Ivy <steveivy@gmail.com>.
    """

    def __init__(self, host='localhost', port=8125, prefix=''):
        # Resolve the host name early.
        info = socket.getaddrinfo(host, int(port), 0, socket.SOCK_DGRAM)
        family, socktype, proto, _canonname, addr = info[0]
        self.addr = addr
        self.log = logger
        self.udp_sock = socket.socket(family, socktype, proto)
        self.random = random.random  # Testing hook
        if prefix and not prefix.endswith('.'):
            prefix = prefix + '.'
        self.prefix = prefix

    def close(self):
        """
        See :meth:`perfmetrics.interfaces.IStatsdClient.close`.

        .. versionadded:: 3.0
        """
        if self.udp_sock:
            self.udp_sock.close()
            self.udp_sock = None

    def timing(self, stat, value, rate=1, buf=None, rate_applied=False):
        """
        See :meth:`perfmetrics.interfaces.IStatsdClient.timing`.

        """
        if rate >= 1 or rate_applied or self.random() < rate:
            s = '%s%s:%d|ms' % (self.prefix, stat, value)
            if buf is None:
                self._send(s)
            else:
                buf.append(s)

    def gauge(self, stat, value, rate=1, buf=None, rate_applied=False):
        """
        See :meth:`perfmetrics.interfaces.IStatsdClient.gauge`.
        """
        if rate >= 1 or rate_applied or self.random() < rate:
            s = '%s%s:%s|g' % (self.prefix, stat, value)
            if buf is None:
                self._send(s)
            else:
                buf.append(s)

    def incr(self, stat, count=1, rate=1, buf=None, rate_applied=False):
        """
        See :meth:`perfmetrics.interfaces.IStatsdClient.incr`.
        """
        if rate >= 1:
            s = '%s%s:%s|c' % (self.prefix, stat, count)
        elif rate_applied or self.random() < rate:
            s = '%s%s:%s|c|@%s' % (self.prefix, stat, count, rate)
        else:
            return

        if buf is None:
            self._send(s)
        else:
            buf.append(s)

    def decr(self, stat, count=1, rate=1, buf=None, rate_applied=False):
        """
        See :meth:`perfmetrics.interfaces.IStatsdClient.decr`.
        """
        self.incr(stat, -count, rate=rate, buf=buf, rate_applied=rate_applied)

    def set_add(self, stat, value, rate=1, buf=None, rate_applied=False):
        """
        See :meth:`perfmetrics.interfaces.IStatsdClient.set_add`.
        """
        if rate >= 1 or rate_applied or self.random() < rate:
            s = '%s%s:%s|s' % (self.prefix, stat, value)
            if buf is None:
                self._send(s)
            else:
                buf.append(s)

    def _send(self, data):
        """Send a UDP packet containing a string."""
        try:
            self.udp_sock.sendto(data.encode('ascii'), self.addr)
        except IOError:
            self.log.exception("Failed to send UDP packet")

    def sendbuf(self, buf):
        """
        See :meth:`perfmetrics.interfaces.IStatsdClient.sendbuf`.
        """
        if buf:
            self._send('\n'.join(buf))


@implementer(IStatsdClient)
class StatsdClientMod(object):
    """
    Wrap `StatsdClient`, modifying all stat names in context.

    .. versionchanged:: 3.0

       The wrapped object's attributes are now accessible on this object.

       This object now uses ``__slots__``.
    """

    __slots__ = (
        '_wrapped',
        'format',
    )

    def __init__(self, wrapped, format):
        self._wrapped = wrapped
        self.format = format

    def close(self):
        self._wrapped.close()

    def __getattr__(self, name):
        return getattr(self._wrapped, name)

    def __setattr__(self, name, value):
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        else:
            setattr(self._wrapped, name, value)

    def timing(self, stat, *args, **kw):
        self._wrapped.timing(self.format % stat, *args, **kw)

    def gauge(self, stat, *args, **kw):
        self._wrapped.gauge(self.format % stat, *args, **kw)

    def incr(self, stat, *args, **kw):
        self._wrapped.incr(self.format % stat, *args, **kw)

    def decr(self, stat, *args, **kw):
        self._wrapped.decr(self.format % stat, *args, **kw)

    def set_add(self, stat, *args, **kw):
        self._wrapped.set_add(self.format % stat, *args, **kw)

    def sendbuf(self, buf):
        self._wrapped.sendbuf(buf)


@implementer(IStatsdClient)
class NullStatsdClient(object):
    """No-op statsd client."""

    def close(self):
        """Does nothing."""

    def timing(self, stat, *args, **kw):
        """Does nothing."""

    def gauge(self, stat, *args, **kw):
        """Does nothing."""

    def incr(self, stat, *args, **kw):
        """Does nothing."""

    def decr(self, stat, *args, **kw):
        """Does nothing."""

    def set_add(self, stat, value, *args, **kw):
        """Does nothing."""

    def sendbuf(self, buf):
        """Does nothing"""


null_client = NullStatsdClient()
