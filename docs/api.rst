===============
 API Reference
===============

.. currentmodule:: perfmetrics


Decorators
==========

.. decorator:: metric

   Notifies Statsd every time the function is called.

   Sends both call counts and timing information.  The name of the metric
   sent to Statsd is ``<module>.<function name>``.

.. decorator:: metricmethod

   Like ``@metric``, but the name of the Statsd metric is
   ``<class module>.<class name>.<method name>``.

.. autoclass:: Metric
.. autoclass:: MetricMod


Functions
=========

.. autofunction:: statsd_client
.. autofunction:: set_statsd_client
.. autofunction:: statsd_client_from_uri


StatsdClient Methods
====================

Python code can send custom metrics by first getting the current
`IStatsdClient` using the `statsd_client()` function.  Note that
`statsd_client()` returns None if no client has been configured.

.. autointerface:: perfmetrics.interfaces.IStatsdClient

There are three implementations of this interface:

.. autoclass:: perfmetrics.statsd.StatsdClient
.. autoclass:: perfmetrics.statsd.StatsdClientMod
.. autoclass:: perfmetrics.statsd.NullStatsdClient


Pyramid Integration
===================

.. autofunction:: includeme
.. autofunction:: tween

WSGI Integration
================

.. autofunction:: make_statsd_app
