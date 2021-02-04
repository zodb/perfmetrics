#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"


from perfmetrics.statsd import StatsdClient

from .observation import Observation


class _TrackingSocket(object):
    """
    Maintain a list of sent packet/address pairs, as well
    as parsed observations/address pairs.
    """
    def __init__(self):
        self.sent_packets = [] # type: List[Tuple[str, bytes]
        self.observations = [] # type: List[Tuple[Observation, bytes]

    def clear(self):
        del self.sent_packets[:]
        del self.observations[:]

    close = clear

    def sendto(self, data, addr):
        # The client encoded to bytes
        assert isinstance(data, bytes)
        # We always want native strings here, that's what the
        # user specified when calling the StatsdClient methods.
        data = data.decode('utf-8') if bytes is not str else data
        self.sent_packets.append((data, addr,))
        for m in Observation.make_all(data):
            self.observations.append((m, addr,))


class FakeStatsDClient(StatsdClient):
    """
    A mock statsd client that tracks sent statsd metrics in memory
    rather than pushing them over a socket. This class is a drop
    in replacement for `perfmetrics.statsd.StatsdClient` that collects statsd
    packets and `~.Observation` that are sent through the client.

    .. versionchanged:: 3.1.0
       Like the normal clients, this object is now always true, whether or
       not any observations have been sent.
    """

    def __init__(self, prefix=''):
        """
        Create a mock statsd client with the given prefix.
        """
        super(FakeStatsDClient, self).__init__(prefix=prefix)

        # Monkey patch the socket to track things in memory instead
        self.udp_sock.close()
        self.udp_sock = _TrackingSocket()

    def clear(self):
        """
        Clears the statsd metrics that have been collected
        """
        self.udp_sock.clear()

    def __bool__(self):
        return True

    __nonzero__ = __bool__ # Python 2

    def __len__(self):
        """
        The number of metrics sent. This accounts for multi metric packets
        that may be sent.
        """
        return len(self.udp_sock.observations)

    def __iter__(self):
        """
        Iterates the `Observations <~.Observation>` provided to this statsd
        client.
        """
        for metric, _ in self.udp_sock.observations:
            yield metric
    iter_observations = __iter__

    def iter_packets(self):
        """
        Iterates the raw statsd packets provided to the statsd client.

        :return: Iterator of native strings.
        """
        for data, _ in self.udp_sock.sent_packets:
            yield data

    @property
    def observations(self):
        """
        A list of `~.Observation` objects collected by this client.

        .. seealso:: `iter_observations`
        """
        return list(self)

    @property
    def packets(self):
        """
        A list of raw statsd packets collected by this client.

        .. seealso:: `iter_packets`
        """
        return list(self.iter_packets())
