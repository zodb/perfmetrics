
# Fork of statsd.py by Steve Ivy <steveivy@gmail.com>, http://monkinetic.com

import logging
import random
import socket


class StatsdClient(object):

    def __init__(self, host='localhost', port=8125):
        """
        Create a new Statsd client.
        * host: the host where statsd is listening, defaults to localhost
        * port: the port where statsd is listening, defaults to 8125

        >>> from pystatsd import statsd
        >>> stats_client = statsd.Statsd(host, port)
        """
        # Pre-resolve the host name.
        info = socket.getaddrinfo(host, int(port), 0, socket.SOCK_DGRAM)
        family, socktype, proto, _canonname, addr = info[0]
        self.addr = addr
        self.log = logging.getLogger(__name__)
        self.udp_sock = socket.socket(family, socktype, proto)
        self.random = random.random

    def timing(self, stat, time, sample_rate=1):
        """
        Log timing information in milliseconds for a single stat
        >>> statsd_client.timing('some.time', 500)
        """
        stats = {stat: "%d|ms" % time}
        self.send(stats, sample_rate)

    def gauge(self, stat, value, sample_rate=1):
        """
        Log a gauge value
        >>> statsd_client.gauge('pool_size', 5)
        """
        self.send({stat: '%s|g' % value}, sample_rate)

    def increment(self, stats, sample_rate=1):
        """
        Increment one or more stats counters
        >>> statsd_client.increment('some.int')
        >>> statsd_client.increment('some.int',0.5)
        """
        self.update_stats(stats, 1, sample_rate=sample_rate)

    def decrement(self, stats, sample_rate=1):
        """
        Decrement one or more stats counters
        >>> statsd_client.decrement('some.int')
        """
        self.update_stats(stats, -1, sample_rate=sample_rate)

    def update_stats(self, stats, delta, sample_rate=1):
        """
        Update one or more stats counters by arbitrary amounts
        >>> statsd_client.update_stats('some.int',10)
        """
        if isinstance(stats, basestring):
            stats = [stats]

        data = dict((stat, "%s|c" % delta) for stat in stats)
        self.send(data, sample_rate)

    def send(self, data, sample_rate=1):
        """
        Squirt the metrics over UDP
        """
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
