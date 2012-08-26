
from decorator import decorator
from metrical.clientstack import client_stack
from time import time
import logging
import random
import socket


cdef class StatsdClient(object):
    """Send packets to statsd.

    Fork of statsd.py by Steve Ivy <steveivy@gmail.com>, http://monkinetic.com
    """
    cdef public object addr, log, udp_sock, random, gauge_suffix

    def __init__(self, host='localhost', port=8125, gauge_suffix=''):
        # Pre-resolve the host name.
        info = socket.getaddrinfo(host, int(port), 0, socket.SOCK_DGRAM)
        family, socktype, proto, _canonname, addr = info[0]
        self.addr = addr
        self.log = logging.getLogger(__name__)
        self.udp_sock = socket.socket(family, socktype, proto)
        self.random = random.random  # Testing hook
        self.gauge_suffix = gauge_suffix

    def timing(self, str stat, int time, double sample_rate=1.0, buf=None):
        """Log timing information in milliseconds for a single stat.

        >>> client.timing('some.time', 500)
        """
        if sample_rate >= 1.0 or self.random() < sample_rate:
            s = '%s:%d|ms' % (stat, time)
            if buf is None:
                self.send(s)
            else:
                buf.append(s)

    def gauge(self, str stat, value, double sample_rate=1.0, buf=None):
        """Log a gauge value.

        >>> client.gauge('pool_size', 5)
        """
        if sample_rate >= 1.0 or self.random() < sample_rate:
            s = '%s%s:%s|g' % (stat, self.gauge_suffix, value)
            if buf is None:
                self.send(s)
            else:
                buf.append(s)

    def inc(self, str stat, double sample_rate=1.0, buf=None):
        """Increment a counter.

        >>> client.inc('some.int')
        >>> client.inc('some.float', 0.5)
        """
        self.change(stat, 1, sample_rate=sample_rate, buf=buf)

    def dec(self, str stat, double sample_rate=1, buf=None):
        """Decrement a counter.

        >>> client.dec('some.int')
        """
        self.change(stat, -1, sample_rate=sample_rate, buf=buf)

    cpdef change(self, str stat, delta, double sample_rate=1.0,
                 buf=None):
        """Change a counter by an arbitrary amount.

        >>> client.change('some.int', 10)
        """
        if sample_rate >= 1.0:
            s = '%s:%s|c' % (stat, delta)
        elif self.random() < sample_rate:
            s = '%s:%s|c|@%s' % (stat, delta, sample_rate)
        else:
            return

        if buf is None:
            self.send(s)
        else:
            buf.append(s)

    cpdef send(self, str data):
        """Send a UDP packet."""
        try:
            self.udp_sock.sendto(data, self.addr)
        except IOError:
            self.log.exception("Failed to send UDP packet")

    def sendbuf(self, buf):
        """Send a UDP packet containing buffered lines."""
        try:
            self.udp_sock.sendto('\n'.join(buf), self.addr)
        except IOError:
            self.log.exception("Failed to send UDP packet")


cdef class Metric(object):
    """A factory of metric decorators."""
    cdef readonly object stat
    cdef readonly double sample_rate
    cdef readonly int method, count, timing

    def __init__(self, stat=None, sample_rate=1.0, method=False,
                 count=True, timing=True):
        self.stat = stat
        self.sample_rate = sample_rate
        self.method = method
        self.count = count
        self.timing = timing

    def __call__(self, f):
        """Decorate a function or method so it can send statistics to statsd.
        """
        return decorator(self.call_with_metric, f)

    def call_with_metric(self, func, *args, **kw):
        client = client_stack.get()
        if client is None:
            # No statsd client has been configured.
            return func(*args, **kw)

        instance_stat = self.stat
        if instance_stat:
            stat = instance_stat
        elif self.method:
            cls = args[0].__class__
            stat = '%s.%s.%s' % (cls.__module__, cls.__name__, func.__name__)
        else:
            stat = '%s.%s' % (func.__module__, func.__name__)

        sample_rate = self.sample_rate

        count = self.count
        if self.timing:
            if count:
                buf = []
                client.change(stat, 1, self.sample_rate, buf=buf)
            else:
                buf = None
            start = time()
            try:
                return func(*args, **kw)
            finally:
                elapsed_ms = int((time() - start) * 1000)
                client.timing(stat, elapsed_ms, self.sample_rate, buf=buf)
                if buf:
                    client.sendbuf(buf)

        else:
            if count:
                client.change(stat, 1, self.sample_rate)
            return func(*args, **kw)
