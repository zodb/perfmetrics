
import logging
import random
import socket


class StatsdClient(object):
    """Send packets to statsd.

    Derived from statsd.py by Steve Ivy <steveivy@gmail.com>.
    """

    def __init__(self, host='localhost', port=8125, prefix='',
                 gauge_suffix=''):
        # Resolve the host name early.
        info = socket.getaddrinfo(host, int(port), 0, socket.SOCK_DGRAM)
        family, socktype, proto, _canonname, addr = info[0]
        self.addr = addr
        self.log = logging.getLogger(__name__)
        self.udp_sock = socket.socket(family, socktype, proto)
        self.random = random.random  # Testing hook
        if prefix and not prefix.endswith('.'):
            prefix = prefix + '.'
        self.prefix = prefix
        if gauge_suffix and not gauge_suffix.startswith('.'):
            gauge_suffix = '.' + gauge_suffix
        self.gauge_suffix = gauge_suffix

    def timing(self, stat, value, rate=1, buf=None, rate_applied=False):
        """Log timing information in milliseconds.

        >>> client.timing('some.time', 500)
        """
        if rate >= 1 or rate_applied or self.random() < rate:
            s = '%s%s:%d|ms' % (self.prefix, stat, value)
            if buf is None:
                self._send(s)
            else:
                buf.append(s)

    def gauge(self, stat, value, suffix=None, rate=1, buf=None,
              rate_applied=False):
        """Log a gauge value.

        >>> client.gauge('pool_size', 5)
        """
        if rate >= 1 or rate_applied or self.random() < rate:
            if suffix is None:
                suffix = self.gauge_suffix or ''
            s = '%s%s%s:%s|g' % (self.prefix, stat, suffix, value)
            if buf is None:
                self._send(s)
            else:
                buf.append(s)

    def incr(self, stat, count=1, rate=1, buf=None, rate_applied=False):
        """Increment a counter.

        >>> client.incr('some.int')
        >>> client.incr('some.float', 0.5)
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
        """Decrement a counter.

        >>> client.decr('some.int')
        """
        self.incr(stat, -count, rate=rate, buf=buf, rate_applied=rate_applied)

    def _send(self, data):
        """Send a UDP packet containing a string."""
        try:
            self.udp_sock.sendto(data.encode('ascii'), self.addr)
        except IOError:
            self.log.exception("Failed to send UDP packet")

    def sendbuf(self, buf):
        """Send a UDP packet containing string lines."""
        try:
            if buf:
                self.udp_sock.sendto('\n'.join(buf).encode('ascii'), self.addr)
        except IOError:
            self.log.exception("Failed to send UDP packet")
