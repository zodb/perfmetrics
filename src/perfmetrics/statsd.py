
import logging
import random
import socket


class StatsdClient(object):
    """Send packets to statsd.

    Derived from statsd.py by Steve Ivy <steveivy@gmail.com>.
    """

    def __init__(self, host='localhost', port=8125, gauge_suffix=''):
        # Pre-resolve the host name.
        info = socket.getaddrinfo(host, int(port), 0, socket.SOCK_DGRAM)
        family, socktype, proto, _canonname, addr = info[0]
        self.addr = addr
        self.log = logging.getLogger(__name__)
        self.udp_sock = socket.socket(family, socktype, proto)
        self.random = random.random  # Testing hook
        self.gauge_suffix = gauge_suffix

    def timing(self, stat, time, sample_rate=1, buf=None):
        """Log timing information in milliseconds for a single stat.

        >>> client.timing('some.time', 500)
        """
        if sample_rate >= 1 or self.random() < sample_rate:
            s = '%s:%d|ms' % (stat, time)
            if buf is None:
                self.send(s)
            else:
                buf.append(s)

    def gauge(self, stat, value, suffix=None, sample_rate=1, buf=None):
        """Log a gauge value.

        >>> client.gauge('pool_size', 5)
        """
        if sample_rate >= 1 or self.random() < sample_rate:
            if suffix is None:
                suffix = self.gauge_suffix or ''
            s = '%s%s:%s|g' % (stat, suffix, value)
            if buf is None:
                self.send(s)
            else:
                buf.append(s)

    def inc(self, stat, sample_rate=1, buf=None):
        """Increment a counter.

        >>> client.inc('some.int')
        >>> client.inc('some.float', 0.5)
        """
        self.change(stat, 1, sample_rate=sample_rate, buf=buf)

    def dec(self, stat, sample_rate=1, buf=None):
        """Decrement a counter.

        >>> client.dec('some.int')
        """
        self.change(stat, -1, sample_rate=sample_rate, buf=buf)

    def change(self, stat, delta, sample_rate=1, buf=None):
        """Change a counter by an arbitrary amount.

        >>> client.change('some.int', 10)
        """
        if sample_rate >= 1:
            s = '%s:%s|c' % (stat, delta)
        elif self.random() < sample_rate:
            s = '%s:%s|c|@%s' % (stat, delta, sample_rate)
        else:
            return

        if buf is None:
            self.send(s)
        else:
            buf.append(s)

    def send(self, data):
        """Send a UDP packet containing a string."""
        try:
            self.udp_sock.sendto(data.encode('utf-8'), self.addr)
        except IOError:
            self.log.exception("Failed to send UDP packet")

    def sendbuf(self, buf):
        """Send a UDP packet containing string lines."""
        try:
            if buf:
                self.udp_sock.sendto('\n'.join(buf).encode('utf-8'), self.addr)
        except IOError:
            self.log.exception("Failed to send UDP packet")
