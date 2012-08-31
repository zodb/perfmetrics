
Introduction
------------

The perfmetrics package provides a simple way to add software performance
metrics to Python libraries and applications.  Use perfmetrics to find the
true bottlenecks in a production application.

The perfmetrics package is a client of the ``statsd`` daemon by Etsy, which
is in turn a client of Graphite (specifically, the Carbon daemon).  Because
the perfmetrics package sends UDP packets to statsd, the overhead of
perfmetrics is negligible and it can work in either threaded (synchronous) or
event-driven (asynchronous) programs.


Usage
-----

Use the @metric and @metricmethod decorators to alter functions and methods
so they can send timing and call statistics to statsd.  Add the decorators
to anything that might be a signficant bottleneck, including library
functions.

.. testcode::

	from perfmetrics import metric
	from perfmetrics import metricmethod

    @metric
    def myfunction():
        """Do something that might be expensive"""

    class MyClass(object):
    	@metricmethod
    	def mymethod(self):
    	    """Do some other possibly expensive thing"""

Next, tell perfmetrics how to connect to statsd.  (Until you do, the
perfmetrics package does not collect or send any metrics.)  Ideally,
your application should read the statsd URI from a configuration file,
but this example uses a hard-coded URI for simplicity.

.. testcode::

    from perfmetrics import set_statsd_client
    set_statsd_client('statsd://localhost:8125')

    for i in xrange(1000):
        myfunction()
        MyClass().mymethod()

If you run that code, it will fire 2000 UDP packets at port
8125.  However, unless you have already installed Graphite and statsd,
all of those packets will be ignored and dropped.  This is a good thing:
you don't want your production application to fail or slow down just
because your performance monitoring software is stopped or not working.

Install Graphite and statsd to receive and graph the metrics.  One good way
to install Graphite is the `graphite_buildout example`_, which can install
Graphite without root access.

.. _`graphite_buildout example`: https://github.com/hathawsh/graphite_buildout


Threading
---------

While most programs send statistics from any thread to a single global
statsd server, some programs need to use a different statsd server
for each thread.  If you only need a global statsd server, use the
``set_statsd_client`` function.  If you need to use a different statsd
server for each thread, use the ``statsd_client_stack`` object, which
supports the ``push``, ``pop``, and ``clear`` methods.


Reference Documentation
-----------------------

Decorators
~~~~~~~~~~

``@metric``: Notifies statsd using UDP every time the function is called.
Sends both call counts and timing information.  The name of the metric
sent to statsd is ``<module>.<function name>``.

``@metricmethod``: like ``metric``, but the name of the metric is
``<class module>.<class name>.<method name>``.

``@Metric(stat=None, sample_rate=1, method=False, count=True, timing=True)``:
A decorator with options.
``stat`` is the name of the metric to send; set it to None to use
the name of the function or method.
``sample_rate`` lets you reduce the number of packets sent to statsd
by selecting a random sample; for example, set it to 0.1 to send
one tenth of the packets.
If the ``method`` parameter is true, the default metric name is based on
the method's class name rather than the module name.
Setting ``count`` to False disables the counter statistics sent to statsd.
Setting ``timing`` to False disables the timing statistics sent to statsd.

If you need to decorate a frequently called function or method,
minimize the decorator's overhead using options of the ``Metric``
decorator instead of ``metric`` or ``metricmethod``.  The example below
uses a static metric name and a sample rate.  It also disables the collection
of timing information, which can take a few nanoseconds to compute.

.. testcode::

	@Metric('frequent_func', sample_rate=0.1, timing=False)
	def frequent_func():
		"""Do something fast and frequently"""


Functions
~~~~~~~~~

``statsd_client()``: Return the currently configured ``StatsdClient``.
Returns the thread-local client if there is one, or the global client
if there is one, or None.

``set_statsd_client(client_or_uri)``: Set the global StatsdClient.  The
``client_or_uri`` can be a StatsdClient, a ``statsd://`` URI, or None.

``statsd_client_from_uri(uri)``: Create a ``StatsdClient`` from a URI.
A typical URI is ``statsd://localhost:8125``.  An optional
query parameter is ``gauge_suffix``.  The default gauge_suffix
is ``.<host_name>``.  See the ``StatsdClient`` documentation for
more information about ``gauge_suffix``.


StatsdClient Methods
~~~~~~~~~~~~~~~~~~~~

Most of the methods below have optional ``sample_rate`` and ``buf``
parameters.  The ``sample_rate`` parameter, when set to a value less than
1, causes StatsdClient to send a random sample of packets rather than every
packet.  If the ``buf`` parameter is a list, StatsdClient appends the packet
contents to the ``buf`` list rather than send the packet, making it
possible to send multiple updates in a single packet.  Keep in mind that
the size of UDP packets is limited (the limit varies by the network, but
1000 bytes is usually a good guess) and any extra bytes will be ignored
silently.

``timing(stat, time, sample_rate=1, buf=None)``: Log timing information.
``stat`` is the name of the metric to record and ``time`` is how long
the measured item took in milliseconds.  Note that
Statsd maintains several data points for each timing metric, so timing
metrics are more expensive than counters or gauges.

``gauge(stat, value, suffix=None, sample_rate=1, buf=None)``:
Update a gauge value.
``stat`` is the name of the metric to record and ``value`` is the new
gauge value.  Because gauges from different machines often conflict, a
suffix is applied to all gauge names.  The default gauge_suffix is based
on the host name.  If the ``suffix`` parameter is not None, it overrides
the default suffix.

``inc(stat, sample_rate=1, buf=None``: Increment a counter.

``dec(stat, sample_rate=1, buf=None``: Decrement a counter.

``change(stat, delta, sample_rate=1, buf=None)``: Change a counter by an
arbitrary amount.  Note that Statsd clears all counter values every time
it sends the metrics to Graphite, which usually happens every 10 seconds.
If you need a persistent value, it may be more appropriate to use a ``gauge``
instead.

``sendbuf(buf)``: Send the contents of the ``buf`` list to Statsd.
