=============
 perfmetrics
=============

The perfmetrics package provides a simple way to add software performance
metrics to Python libraries and applications.  Use perfmetrics to find the
true bottlenecks in a production application.

The perfmetrics package is a client of the Statsd daemon by Etsy, which
is in turn a client of Graphite (specifically, the Carbon daemon).  Because
the perfmetrics package sends UDP packets to Statsd, perfmetrics adds
no I/O delays to applications and little CPU overhead.  It can work
equally well in threaded (synchronous) or event-driven (asynchronous)
software.

Complete documentation is hosted at https://perfmetrics.readthedocs.io

.. image:: https://img.shields.io/pypi/v/perfmetrics.svg
   :target: https://pypi.org/project/perfmetrics/
   :alt: Latest release

.. image:: https://img.shields.io/pypi/pyversions/perfmetrics.svg
   :target: https://pypi.org/project/perfmetrics/
   :alt: Supported Python versions

.. image:: https://github.com/zodb/perfmetrics/workflows/tests/badge.svg
   :target: https://github.com/zodb/perfmetrics/actions?query=workflow%3Atests
   :alt: CI Build Status

.. image:: https://coveralls.io/repos/github/zodb/perfmetrics/badge.svg
   :target: https://coveralls.io/github/zodb/perfmetrics
   :alt: Code Coverage

.. image:: https://readthedocs.org/projects/perfmetrics/badge/?version=latest
   :target: https://perfmetrics.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

Usage
=====

Use the ``@metric`` and ``@metricmethod`` decorators to wrap functions
and methods that should send timing and call statistics to Statsd.
Add the decorators to any function or method that could be a bottleneck,
including library functions.

.. caution::

   These decorators are generic and cause the actual function
   signature to be lost, replaced with ``*args, **kwargs``. This can
   break certain types of introspection, including `zope.interface
   validation <https://github.com/zodb/perfmetrics/issues/15>`_. As a
   workaround, setting the environment variable
   ``PERFMETRICS_DISABLE_DECORATOR`` *before* importing perfmetrics or
   code that uses it will cause ``@perfmetrics.metric``, ``@perfmetrics.metricmethod``,
   ``@perfmetrics.Metric(...)`` and ``@perfmetrics.MetricMod(...)`` to
   return the original function unchanged.

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
