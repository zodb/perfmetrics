
Introduction
============

The perfmetrics package provides a simple way to add software performance
metrics to Python libraries and applications.  Use perfmetrics to find the
true bottlenecks in a production application.

The perfmetrics package is a client of the Statsd daemon by Etsy, which
is in turn a client of Graphite (specifically, the Carbon daemon).  Because
the perfmetrics package sends UDP packets to Statsd, perfmetrics adds
no I/O delays to applications and little CPU overhead.  It can work
equally well in threaded (synchronous) or event-driven (asynchronous)
software.

|TravisBadge|_

.. |TravisBadge| image:: https://secure.travis-ci.org/hathawsh/perfmetrics.png?branch=master
.. _TravisBadge: http://travis-ci.org/hathawsh/perfmetrics


Usage
=====

Use the ``@metric`` and ``@metricmethod`` decorators to wrap functions
and methods that should send timing and call statistics to Statsd.
Add the decorators to any function or method that could be a bottleneck,
including library functions.

Sample::

    from perfmetrics import metric
    from perfmetrics import metricmethod

    @metric
    def myfunction():
        """Do something that might be expensive"""

    class MyClass(object):
    	@metricmethod
    	def mymethod(self):
    	    """Do some other possibly expensive thing"""

Next, tell perfmetrics how to connect to Statsd.  (Until you do, the
decorators have no effect.)  Ideally, either your application should read the
Statsd URI from a configuration file at startup time, or you should set
the STATSD_URI environment variable.  The example below uses a
hard-coded URI::

    from perfmetrics import set_statsd_client
    set_statsd_client('statsd://localhost:8125')

    for i in xrange(1000):
        myfunction()
        MyClass().mymethod()

If you run that code, it will fire 2000 UDP packets at port
8125.  However, unless you have already installed Graphite and Statsd,
all of those packets will be ignored and dropped.  Dropping is a good thing:
you don't want your production application to fail or slow down just
because your performance monitoring system is stopped or not working.

Install Graphite and Statsd to receive and graph the metrics.  One good way
to install them is the `graphite_buildout example`_ at github, which
installs Graphite and Statsd in a custom location without root access.

.. _`graphite_buildout example`: https://github.com/hathawsh/graphite_buildout


Pyramid and WSGI
================

If you have a Pyramid app, you can set the ``statsd_uri`` for each
request by including perfmetrics in your configuration::

    config = Configuration(...)
    config.include('perfmetrics')

Also add a ``statsd_uri`` setting such as ``statsd://localhost:8125``.
Once configured, the perfmetrics tween will set up a Statsd client for
the duration of each request.  This is especially useful if you run
multiple apps in one Python interpreter and you want a different
``statsd_uri`` for each app.

Similar functionality exists for WSGI apps.  Add the app to your Paste Deploy
pipeline::

    [statsd]
    use = egg:perfmetrics#statsd
    statsd_uri = statsd://localhost:8125

    [pipeline:main]
    pipeline =
        statsd
        egg:myapp#myentrypoint


Threading
=========

While most programs send metrics from any thread to a single global
Statsd server, some programs need to use a different Statsd server
for each thread.  If you only need a global Statsd server, use the
``set_statsd_client`` function at application startup.  If you need
to use a different Statsd server for each thread, use the
``statsd_client_stack`` object in each thread.  Use the
``push``, ``pop``, and ``clear`` methods.


Graphite Tips
=============

Graphite stores each metric as a time series with multiple
resolutions.  The sample graphite_buildout stores 10 second resolution
for 48 hours, 1 hour resolution for 31 days, and 1 day resolution for 5 years.
To produce a coarse grained value from a fine grained value, Graphite computes
the mean value (average) for each time span.

Because Graphite computes mean values implicitly, the most sensible way to
treat counters in Graphite is as a "hits per second" value.  That way,
a graph can produce correct results no matter which resolution level
it uses.

Treating counters as hits per second has unfortunate consequences, however.
If some metric sees a 1000 hit spike in one second, then falls to zero for
at least 9 seconds, the Graphite chart for that metric will show a spike
of 100, not 1000, since Graphite receives metrics every 10 seconds and the
spike looks to Graphite like 100 hits per second over a 10 second period.

If you want your graph to show 1000 hits rather than 100 hits per second,
apply the Graphite ``hitcount()`` function, using a resolution of
10 seconds or more.  The hitcount function converts per-second
values to approximate raw hit counts.  Be sure
to provide a resolution value large enough to be represented by at least
one pixel width on the resulting graph, otherwise Graphite will compute
averages of hit counts and produce a confusing graph.

It usually makes sense to treat null values in Graphite as zero, though
that is not the default; by default, Graphite draws nothing for null values.
You can turn on that option for each graph.


Reference Documentation
=======================

Decorators
----------

@metric
    Notifies Statsd using UDP every time the function is called.
    Sends both call counts and timing information.  The name of the metric
    sent to Statsd is ``<module>.<function name>``.

@metricmethod
    Like ``@metric``, but the name of the Statsd metric is
    ``<class module>.<class name>.<method name>``.

Metric(stat=None, rate=1, method=False, count=True, timing=True)
    A decorator or context manager with options.

    ``stat`` is the name of the metric to send; set it to None to use
    the name of the function or method.
    ``rate`` lets you reduce the number of packets sent to Statsd
    by selecting a random sample; for example, set it to 0.1 to send
    one tenth of the packets.
    If the ``method`` parameter is true, the default metric name is based on
    the method's class name rather than the module name.
    Setting ``count`` to False disables the counter statistics sent to Statsd.
    Setting ``timing`` to False disables the timing statistics sent to Statsd.

    Sample use as a decorator::

        @Metric('frequent_func', rate=0.1, timing=False)
        def frequent_func():
            """Do something fast and frequently"""

    Sample use as a context manager::

        def do_something():
            with Metric('doing_something'):
                pass

    If perfmetrics sends packets too frequently, UDP packets may be lost
    and the application performance may be affected.  You can reduce
    the number of packets and the CPU overhead using the ``Metric``
    decorator with options instead of ``metric`` or ``metricmethod``.
    The decorator example above uses a sample rate and a static metric name.
    It also disables the collection of timing information.

    When using Metric as a context manager, you must provide the
    ``stat`` parameter or nothing will be recorded.


Functions
---------

statsd_client()
    Return the currently configured ``StatsdClient``.
    Returns the thread-local client if there is one, or the global client
    if there is one, or None.

set_statsd_client(client_or_uri)
    Set the global ``StatsdClient``.  The
    ``client_or_uri`` can be a StatsdClient, a ``statsd://`` URI, or None.
    Note that when the perfmetrics module is imported, it looks for the
    ``STATSD_URI`` environment variable and calls set_statsd_client()
    if that variable is found.

statsd_client_from_uri(uri)
    Create a ``StatsdClient`` from a URI, but do not install it as the
    global StatsdClient.
    A typical URI is ``statsd://localhost:8125``.  Supported optional
    query parameters are ``prefix`` and ``gauge_suffix``.  The default
    prefix is empty and the default gauge_suffix
    is ``.<host_name>``.  See the ``StatsdClient`` documentation for
    more information about ``gauge_suffix``.


StatsdClient Methods
--------------------

Python code can send custom metrics by first getting the current
``StatsdClient`` using the ``statsd_client()`` function.  Note that
``statsd_client()`` returns None if no client has been configured.

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

timing(stat, value, rate=1, buf=None, rate_applied=False)
    Record timing information.
    ``stat`` is the name of the metric to record and ``value`` is the
    timing measurement in milliseconds.  Note that
    Statsd maintains several data points for each timing metric, so timing
    metrics can take more disk space than counters or gauges.

gauge(stat, value, suffix=None, rate=1, buf=None, rate_applied=False)
    Update a gauge value.
    ``stat`` is the name of the metric to record and ``value`` is the new
    gauge value.  A gauge represents a persistent value such as a pool size.
    Because gauges from different machines often conflict, a
    suffix is usually applied to gauge names.  If the ``suffix``
    parameter is a string (including an empty string), it overrides the
    default gauge suffix.

incr(stat, count=1, rate=1, buf=None, rate_applied=False)
    Increment a counter by ``count``.  Note that Statsd clears all counter
    values every time it sends the metrics to Graphite, which usually
    happens every 10 seconds.  If you need a persistent value, it may
    be more appropriate to use a gauge instead of a counter.

decr(stat, count=1, rate=1, buf=None, rate_applied=False)
    Decrement a counter by ``count``.

sendbuf(buf)
    Send the contents of the ``buf`` list to Statsd.
