
# Fork of statsd.py by Steve Ivy <steveivy@gmail.com>, http://monkinetic.com

import logging
import random
import socket
import urlparse


if 'statsd' not in urlparse.uses_query:
    urlparse.uses_query.append('statsd')


def statsd_client_from_uri(uri):
    """Create and return StatsdClient.

    >>> from metrical.statsdclient import statsd_client_from_uri
    >>> client = statsd_client_from_uri('statsd://localhost:8125')
    """
    parts = urlparse.urlsplit(uri)
    if parts.scheme == 'statsd':
        gauge_suffix = '.%s' % socket.gethostname()
        kw = {'gauge_suffix': gauge_suffix}
        if parts.query:
            kw.update(urlparse.parse_qsl(parts.query))
        return StatsdClient(parts.hostname, parts.port, **kw)
    else:
        raise ValueError("URI scheme not supported: %s" % uri)


class StatsdClient(object):

    def __init__(self, host='localhost', port=8125, gauge_suffix=''):
        # Pre-resolve the host name.
        info = socket.getaddrinfo(host, int(port), 0, socket.SOCK_DGRAM)
        family, socktype, proto, _canonname, addr = info[0]
        self.addr = addr
        self.log = logging.getLogger(__name__)
        self.udp_sock = socket.socket(family, socktype, proto)
        self.random = random.random  # Testing hook
        self.gauge_suffix = gauge_suffix

    def timing(self, stat, time, sample_rate=1):
        """Log timing information in milliseconds for a single stat.

        >>> client.timing('some.time', 500)
        """
        stats = {stat: "%d|ms" % time}
        self.send(stats, sample_rate)

    def gauge(self, stat, value, sample_rate=1):
        """Log a gauge value.

        >>> client.gauge('pool_size', 5)
        """
        self.send({stat + self.gauge_suffix: '%s|g' % value}, sample_rate)

    def increment(self, stats, sample_rate=1):
        """Increment one or more stats counters.

        >>> client.increment('some.int')
        >>> client.increment('some.int',0.5)
        """
        self.update_stats(stats, 1, sample_rate=sample_rate)

    def decrement(self, stats, sample_rate=1):
        """Decrement one or more stats counters.

        >>> client.decrement('some.int')
        """
        self.update_stats(stats, -1, sample_rate=sample_rate)

    def update_stats(self, stats, delta, sample_rate=1):
        """Update one or more stats counters by arbitrary amounts.

        >>> client.update_stats('some.int',10)
        """
        if isinstance(stats, basestring):
            stats = [stats]

        data = dict((stat, "%s|c" % delta) for stat in stats)
        self.send(data, sample_rate)

    def send(self, data, sample_rate=1):
        """Send metrics over UDP."""
        # data is a mapping.
        if sample_rate < 1:
            if self.random() > sample_rate:
                return
            sampled_data = dict((stat, "%s|@%s" % (value, sample_rate))
                                for stat, value in data.iteritems())
        else:
            sampled_data = data

        try:
            for stat, value in sampled_data.iteritems():
                self.udp_sock.sendto("%s:%s" % (stat, value), self.addr)
        except IOError:
            self.log.exception("Failed to send UDP packet")
